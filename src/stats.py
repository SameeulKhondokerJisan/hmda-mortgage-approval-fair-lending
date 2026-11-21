"""Statistics used by the fair-lending analysis, written out so each step can be checked.

* wilson(): Wilson score interval for a proportion.
* design(): applicant group dummies and underwriting controls as a numeric matrix.
* ols(): least squares with one absorbed fixed effect (exact within transformation) and
  cluster-robust standard errors. Used as a linear probability model for denial (coefficients are
  percentage-point differences) and for pricing.
* oaxaca(): two-group Oaxaca-Blinder decomposition with pooled coefficients and a group indicator,
  so explained + unexplained equals the raw gap exactly.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats as st

GROUP_DUMMIES = ["Black", "Hispanic", "Asian", "Other minority"]
REFERENCES = {"dti_band": "3 30-35%", "ltv_band": "2 60-80%", "loan_type": "Conventional", "sex": "Male",
              "age_band": "35-44", "tract_income_band": "3 Middle (80-120%)"}
BLOCKS = {"dti_band": "Debt-to-income", "ltv_band": "Loan-to-value", "loan_type": "Loan type",
          "sex": "Age and sex", "age_band": "Age and sex", "tract_income_band": "Neighbourhood income",
          "log_income": "Income and loan size", "log_loan": "Income and loan size",
          "log_property": "Income and loan size", "conforming": "Income and loan size",
          "direct_application": "Application channel",
          "points_pct": "Discount points"}


def wilson(k, n, z: float = 1.96) -> tuple[np.ndarray, np.ndarray]:
    k, n = np.asarray(k, dtype=float), np.asarray(n, dtype=float)
    p = k / n
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return centre - half, centre + half


def _dummies(series: pd.Series, reference: str, prefix: str) -> pd.DataFrame:
    values = series.astype(str)
    levels = [v for v in sorted(values.unique()) if v != reference]
    return pd.DataFrame({f"{prefix}={lv}": (values == lv).to_numpy(dtype=np.float64) for lv in levels},
                        index=series.index)


def design(df: pd.DataFrame, controls: bool = True, groups: list[str] | None = None,
           pricing: bool = False) -> pd.DataFrame:
    """Group dummies (reference: White) plus, if controls, the underwriting controls."""
    groups = GROUP_DUMMIES if groups is None else groups
    g = df["applicant_group"].astype(str)
    parts = [pd.DataFrame({f"group={x}": (g == x).to_numpy(dtype=np.float64) for x in groups}, index=df.index)]
    if controls:
        cats = ["dti_band", "ltv_band", "loan_type", "sex", "age_band", "tract_income_band"]
        if pricing:
            cats.remove("loan_type")
        parts += [_dummies(df[c], REFERENCES[c], c) for c in cats]
        num = pd.DataFrame({"log_income": np.log(df["income_k"].to_numpy(dtype=float)),
                            "log_loan": np.log(df["loan_amount"].to_numpy(dtype=float)),
                            "log_property": np.log(df["property_value"].to_numpy(dtype=float)),
                            "conforming": df["conforming"].to_numpy(dtype=float),
                            "direct_application": df["direct_application"].to_numpy(dtype=float)}, index=df.index)
        if pricing:
            pts = df["discount_points"].fillna(0).to_numpy(dtype=float) / df["loan_amount"].to_numpy(dtype=float)
            num["points_pct"] = 100 * pts
        parts.append(num)
    X = pd.concat(parts, axis=1)
    keep = X.columns[(X != 0).any() & (X.nunique() > 1)]
    return X[keep]


@dataclass
class OLSResult:
    coef: pd.DataFrame        # term, coef, se, t, p, ci_low, ci_high
    n: int
    clusters: int
    r2_within: float
    absorbed_groups: int


def _group_means(M: np.ndarray, codes: np.ndarray, counts: np.ndarray) -> np.ndarray:
    out = np.empty_like(M)
    for j in range(M.shape[1]):
        out[:, j] = np.bincount(codes, weights=M[:, j], minlength=len(counts))[codes] / counts[codes]
    return out


def ols(y, X: pd.DataFrame, absorb=None, cluster=None) -> OLSResult:
    """OLS of y on X with one absorbed fixed effect and cluster-robust (CR1) standard errors.

    absorb: array of group labels; the model is estimated on deviations from group means (singleton
    groups dropped). Without absorb an intercept is added. cluster: array of cluster labels
    (heteroskedasticity-robust HC1 errors when None).
    """
    yv = np.asarray(y, dtype=np.float64)
    names = list(X.columns)
    M = np.column_stack([yv, X.to_numpy(dtype=np.float64)])
    keep = np.isfinite(M).all(axis=1)
    groups = 0
    if absorb is not None:
        codes, uniques = pd.factorize(np.asarray(absorb)[keep])
        counts = np.bincount(codes)
        nonsingle = counts[codes] > 1
        idx = np.flatnonzero(keep)
        keep = np.zeros(len(yv), dtype=bool)
        keep[idx[nonsingle]] = True
        codes, uniques = pd.factorize(np.asarray(absorb)[keep])
        counts = np.bincount(codes)
        groups = len(uniques)
        M = M[keep]
        M = M - _group_means(M, codes, counts)
    else:
        M = np.column_stack([M[keep], np.ones(keep.sum())])
        names = names + ["intercept"]
    yd, Xd = M[:, 0], M[:, 1:]
    # drop columns with no variation left (absorbed by the fixed effect)
    var = Xd.std(axis=0) > 1e-12
    if absorb is None:
        var[-1] = True
    Xd = Xd[:, var]
    names = [n for n, v in zip(names, var) if v]
    n, k = Xd.shape
    XtX = Xd.T @ Xd
    XtX_inv = np.linalg.pinv(XtX)
    beta = XtX_inv @ (Xd.T @ yd)
    u = yd - Xd @ beta
    if cluster is not None:
        cl, _ = pd.factorize(np.asarray(cluster)[keep])
        G = cl.max() + 1
        S = np.column_stack([np.bincount(cl, weights=Xd[:, j] * u, minlength=G) for j in range(k)])
        meat = S.T @ S
        c = G / (G - 1) * (n - 1) / (n - k)
    else:
        G = n
        meat = (Xd * u[:, None] ** 2).T @ Xd
        c = n / (n - k)
    V = c * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.clip(np.diag(V), 0, None))
    t = beta / np.where(se > 0, se, np.nan)
    dof = (G - 1) if cluster is not None else (n - k)
    p = 2 * st.t.sf(np.abs(t), dof)
    q = st.t.ppf(0.975, dof)
    coef = pd.DataFrame({"term": names, "coef": beta, "se": se, "t": t, "p": p,
                         "ci_low": beta - q * se, "ci_high": beta + q * se})
    r2 = 1 - (u @ u) / ((yd - yd.mean()) @ (yd - yd.mean()))
    return OLSResult(coef, int(n), int(G), float(r2), groups)


def oaxaca(df: pd.DataFrame, group: str, y: str = "denied", reference: str = "White") -> dict:
    """Pooled two-fold decomposition of the mean gap in y between group and reference."""
    sub = df[df["applicant_group"].astype(str).isin([group, reference])]
    X = design(sub, controls=True, groups=[group])
    res = ols(sub[y], X, cluster=sub["lei"].astype(str))
    beta = res.coef.set_index("term").coef
    is_g = (sub["applicant_group"].astype(str) == group).to_numpy()
    diff = X[is_g].mean() - X[~is_g].mean()
    controls = [c for c in X.columns if not c.startswith("group=")]
    contrib = diff[controls] * beta[controls]
    blocks = {}
    for term, value in contrib.items():
        key = BLOCKS[term.split("=")[0]]
        blocks[key] = blocks.get(key, 0.0) + float(value)
    gap = float(sub.loc[is_g, y].mean() - sub.loc[~is_g, y].mean())
    row = res.coef.set_index("term").loc[f"group={group}"]
    return {"group": group, "raw_gap": gap, "explained": float(contrib.sum()), "unexplained": float(row.coef),
            "unexplained_ci_low": float(row.ci_low), "unexplained_ci_high": float(row.ci_high),
            "blocks": dict(sorted(blocks.items(), key=lambda kv: -abs(kv[1]))), "n": res.n}
