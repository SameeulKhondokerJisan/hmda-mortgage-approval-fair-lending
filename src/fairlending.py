"""Fair-lending screens on the 2025 HMDA home-purchase data.

1. Raw approval and denial rates by applicant group, with Wilson intervals and adverse impact ratios.
2. Denial gap ladder: the Black, Hispanic, Asian and other-minority gaps against White applicants as
   underwriting controls, lender x state and lender x county fixed effects are added (linear probability
   model, errors clustered by lender).
3. Logistic regression on a random sample as a robustness check (average marginal effects).
4. Oaxaca-Blinder decomposition of the raw gaps into a part explained by underwriting factors and a
   part that is not.
5. Pricing gaps on originated conventional 30-year fixed loans (rate spread, basis points).
6. Neighbourhood screen: denial by census-tract minority share after applicant controls.
7. Lender screen: within-lender adjusted gaps for the largest lenders.

HMDA has no credit scores, so every adjusted gap is a screening statistic, not proof of discrimination.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src import config
from src.stats import GROUP_DUMMIES, design, ols, oaxaca, wilson


def group_rates(rates: pd.DataFrame) -> pd.DataFrame:
    """Add Wilson intervals and ratios to the reference group (approval AIR and denial-rate ratio)."""
    r = rates[rates.loan_type == "All"].copy()
    r["denial_ci_low"], r["denial_ci_high"] = wilson(r.denied, r.applications)
    ref = r.set_index("applicant_group").loc[config.REFERENCE_GROUP]
    r["approval_air"] = r.approval_rate / ref.approval_rate
    r["denial_ratio"] = r.denial_rate / ref.denial_rate
    r["below_four_fifths"] = r.approval_air < config.FOUR_FIFTHS
    r["order"] = r.applicant_group.map({g: i for i, g in enumerate(config.GROUP_ORDER)})
    return r.sort_values("order").drop(columns="order").reset_index(drop=True)


def _codes(*cols: pd.Series) -> np.ndarray:
    key = cols[0].astype(str)
    for c in cols[1:]:
        key = key + "|" + c.astype(str)
    return key.to_numpy()


def gap_ladder(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    lender = df.lei.astype(str).to_numpy()
    specs = [
        ("1 Raw gap", design(df, controls=False), None),
        ("2 + underwriting controls", design(df), None),
        ("3 + lender x state", design(df), _codes(df.lei, df.state_code)),
        ("4 + lender x county", design(df), _codes(df.lei, df.county_fips)),
    ]
    rows, fits = [], {}
    for name, X, absorb in specs:
        res = ols(df.denied, X, absorb=absorb, cluster=lender)
        c = res.coef.set_index("term")
        for g in GROUP_DUMMIES:
            if f"group={g}" in c.index:
                rows.append({"spec": name, "group": g, **c.loc[f"group={g}", ["coef", "se", "ci_low", "ci_high", "p"]]})
        fits[name] = {"n": res.n, "clusters": res.clusters, "absorbed_groups": res.absorbed_groups,
                      "r2_within": res.r2_within, "regressors": int(len(c))}
        print(f"  gap ladder: {name} done (n={res.n:,})", flush=True)
    return pd.DataFrame(rows), fits


def logit_check(df: pd.DataFrame) -> pd.DataFrame:
    """Logit with controls and state dummies on a random sample: average marginal effect of each group.

    The marginal effect of group g is the mean over all sampled applicants of P(deny | g) - P(deny | White)
    with every other characteristic held at the applicant's own values; the interval uses the delta method.
    """
    sample = df.sample(n=min(config.LOGIT_SAMPLE, len(df)), random_state=config.SEED)
    X = design(sample)
    st_codes = sample.state_code.astype(str)
    big = st_codes.value_counts()
    st_codes = st_codes.where(st_codes.map(big) >= 500, "other")
    states = pd.get_dummies(st_codes, prefix="state", dtype=float)
    states = states.drop(columns=states.sum().idxmax())
    X = pd.concat([X, states], axis=1)
    X = sm.add_constant(X.loc[:, X.std() > 0])
    model = sm.Logit(sample.denied.to_numpy(dtype=float), X).fit(disp=False, maxiter=100, method="newton")
    beta, cov = model.params.to_numpy(), model.cov_params().to_numpy()
    Xv = X.to_numpy(dtype=np.float64)
    gcols = [i for i, c in enumerate(X.columns) if c.startswith("group=")]
    X0 = Xv.copy()
    X0[:, gcols] = 0.0
    xb0 = X0 @ beta
    p0 = 1 / (1 + np.exp(-xb0))
    out = []
    for g in GROUP_DUMMIES:
        term = f"group={g}"
        if term not in X.columns:
            continue
        j = X.columns.get_loc(term)
        xb1 = xb0 + beta[j]
        p1 = 1 / (1 + np.exp(-xb1))
        ame = float((p1 - p0).mean())
        grad = ((p1 * (1 - p1))[:, None] * X0).mean(axis=0) - ((p0 * (1 - p0))[:, None] * X0).mean(axis=0)
        grad[j] += float((p1 * (1 - p1)).mean())
        se = float(np.sqrt(grad @ cov @ grad))
        out.append({"group": g, "ame": ame, "ci_low": ame - 1.96 * se, "ci_high": ame + 1.96 * se,
                    "odds_ratio": float(np.exp(beta[j]))})
    return pd.DataFrame(out).assign(n=len(sample), converged=bool(model.mle_retvals["converged"]))


def decompositions(df: pd.DataFrame) -> list[dict]:
    return [oaxaca(df, g) for g in ("Black", "Hispanic", "Asian")]


def pricing(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Rate spread gaps (basis points) on originated conventional 30-year fixed-rate, fully amortizing loans."""
    p = df[(df.originated == 1) & (df.loan_type.astype(str) == "Conventional") & (df.loan_term == 360)
           & df.fixed_amortizing.fillna(False).astype(bool) & df.rate_spread.notna()
           & df.rate_spread.between(-5, 10)].copy()
    y = p.rate_spread * 100
    lender = p.lei.astype(str).to_numpy()
    specs = [("1 Raw gap", design(p, controls=False), None),
             ("2 + underwriting controls", design(p, pricing=True), None),
             ("3 + lender x state", design(p, pricing=True), _codes(p.lei, p.state_code))]
    rows, fits = [], {}
    for name, X, absorb in specs:
        res = ols(y, X, absorb=absorb, cluster=lender)
        c = res.coef.set_index("term")
        for g in GROUP_DUMMIES:
            if f"group={g}" in c.index:
                rows.append({"spec": name, "group": g, **c.loc[f"group={g}", ["coef", "se", "ci_low", "ci_high", "p"]]})
        fits[name] = {"n": res.n, "clusters": res.clusters}
    stats = {"loans": int(len(p)), "median_rate_spread_bps": float(y.median()),
             "median_interest_rate": float(p.interest_rate.median()),
             "mean_rate_spread_bps_by_group": {g: float(v) for g, v in
                                               (p.groupby(p.applicant_group.astype(str)).rate_spread.mean() * 100).items()}}
    return pd.DataFrame(rows), {"fits": fits, **stats}


def neighbourhood(df: pd.DataFrame) -> pd.DataFrame:
    """Denial by tract minority share, net of applicant group, controls and lender x state effects."""
    d = df[df.tract_minority_band.astype(str) != "6 Unknown"]
    X = design(d)
    tracts = pd.get_dummies(d.tract_minority_band.astype(str), prefix="tract", dtype=float).drop(columns="tract_1 <10%")
    X = pd.concat([X, tracts], axis=1)
    res = ols(d.denied, X, absorb=_codes(d.lei, d.state_code), cluster=d.lei.astype(str).to_numpy())
    c = res.coef[res.coef.term.str.startswith("tract_")].copy()
    c["tract_minority_band"] = c.term.str.replace("tract_", "", regex=False)
    raw = d.groupby(d.tract_minority_band.astype(str)).denied.agg(["mean", "size"]).reset_index()
    raw.columns = ["tract_minority_band", "raw_denial_rate", "applications"]
    base = raw.set_index("tract_minority_band").loc["1 <10%", "raw_denial_rate"]
    raw["raw_gap"] = raw.raw_denial_rate - base
    return raw.merge(c[["tract_minority_band", "coef", "ci_low", "ci_high"]], on="tract_minority_band", how="left")


def lender_screen(df: pd.DataFrame, lenders: pd.DataFrame) -> pd.DataFrame:
    """Within-lender gaps (controls + county fixed effects, errors clustered by county) for large lenders."""
    counts = df.groupby("lei", observed=True).applicant_group.value_counts().unstack(fill_value=0)
    total = counts.sum(axis=1)
    eligible = counts[(total >= config.MIN_LENDER_APPS) & (counts.get("Black", 0) >= config.MIN_LENDER_GROUP_APPS)
                      & (counts.get("Hispanic", 0) >= config.MIN_LENDER_GROUP_APPS)].index
    names = lenders.set_index("lei").lender_name
    rows = []
    for lei in eligible:
        d = df[df.lei == lei]
        X = design(d, groups=["Black", "Hispanic", "Asian"])
        res = ols(d.denied, X, absorb=d.county_fips.astype(str).to_numpy(), cluster=d.county_fips.astype(str).to_numpy())
        c = res.coef.set_index("term")
        row = {"lei": lei, "lender_name": names.get(lei, lei), "applications": int(len(d)),
               "denial_rate": float(d.denied.mean()), "counties": res.clusters}
        for g in ("Black", "Hispanic"):
            raw = float(d.denied[d.applicant_group.astype(str) == g].mean()
                        - d.denied[d.applicant_group.astype(str) == "White"].mean())
            row[f"raw_gap_{g.lower()}"] = raw
            if f"group={g}" in c.index:
                r = c.loc[f"group={g}"]
                row[f"adj_gap_{g.lower()}"], row[f"ci_low_{g.lower()}"], row[f"ci_high_{g.lower()}"] = \
                    float(r.coef), float(r.ci_low), float(r.ci_high)
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["screen"] = np.where((out.ci_low_black > 0) | (out.ci_low_hispanic > 0), "Gap above zero: review files",
                             "No gap distinguishable from zero")
    return out.sort_values("applications", ascending=False).reset_index(drop=True)


def simulate_policy(grid: pd.DataFrame, dti_max: int = 9, ltv_max: int = 7, missing_passes: bool = True) -> pd.DataFrame:
    """Python twin of the Excel simulator: approvals by group if applications above the caps were turned away.

    dti_max / ltv_max are the highest band orders allowed (see the band prefixes in sql/02_applications.sql);
    9 and 7 mean no cap. Denied applications stay denied; approved ones above a cap are lost.
    """
    g = grid.copy()
    g["dti_order"] = g.dti_band.str[0].astype(int)
    g["ltv_order"] = g.ltv_band.str[0].astype(int)
    ok_dti = (g.dti_order <= dti_max) | ((g.dti_order == 9) & missing_passes)
    ok_ltv = (g.ltv_order <= ltv_max) | ((g.ltv_order == 7) & missing_passes)
    g["approved_after"] = g.approved * (ok_dti & ok_ltv)
    g["volume_after"] = g.approved_volume * (ok_dti & ok_ltv)
    s = g.groupby("applicant_group")[["applications", "approved", "approved_after", "approved_volume",
                                      "volume_after"]].sum()
    s["approval_rate"], s["approval_rate_after"] = s.approved / s.applications, s.approved_after / s.applications
    ref = s.loc[config.REFERENCE_GROUP]
    s["air"], s["air_after"] = s.approval_rate / ref.approval_rate, s.approval_rate_after / ref.approval_rate_after
    s["approvals_lost"] = s.approved - s.approved_after
    s["share_lost"] = s.approvals_lost / s.approved
    s["volume_lost"] = s.approved_volume - s.volume_after
    return s.reset_index()
