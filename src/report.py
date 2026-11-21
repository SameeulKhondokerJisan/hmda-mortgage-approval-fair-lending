"""Render README.md and reports/memo.md from reports/results.json (numbers never typed by hand)."""
from __future__ import annotations

from src import config


def _p(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%"


def _pp(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f} pp"


def _usd(x: float) -> str:
    if abs(x) >= 1e12:
        return f"${x / 1e12:,.2f} trillion"
    if abs(x) >= 1e9:
        return f"${x / 1e9:,.1f} billion"
    if abs(x) >= 1e6:
        return f"${x / 1e6:,.0f} million"
    return f"${x:,.0f}"


def _ci(lo: float, hi: float, scale: float = 100, unit: str = "") -> str:
    return f"95% CI {lo * scale:.1f} to {hi * scale:.1f}{unit}"


def render(results: dict) -> None:
    b, rc = results["business"], results["row_counts"]
    g = {r["applicant_group"]: r for r in results["groups"]["rates"]}
    cliff, reasons = results["dti_cliff"], results["denial_reasons"]
    lad = {(r["spec"][0], r["group"]): r for r in results["gap_ladder"]["rows"]}
    expl = results["gap_ladder"]["share_explained_by_controls"]
    oax = {o["group"]: o for o in results["oaxaca"]}
    pr = results["pricing"]
    prow = {(r["spec"][0], r["group"]): r for r in pr["rows"]}
    hood = {r["tract_minority_band"]: r for r in results["neighbourhood"]}
    ls = results["lender_screen"]
    logit = {r["group"]: r for r in results["logit"]}
    mf = results["model_frame"]
    scen = results["policy_scenarios"]
    w, bl, hi, asn = g["White"], g["Black"], g["Hispanic"], g["Asian"]
    lowest_air = min((g[x] for x in config.GROUPS), key=lambda r: r["approval_air"])

    def join(items: list[str]) -> str:
        return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]

    def share_word(x: float) -> str:
        return ("most" if x >= 0.6 else "about half" if x >= 0.4 else "about a third" if x >= 0.25
                else "a small part")

    def sig(lo: float, hi_: float) -> bool:
        return lo > 0 or hi_ < 0

    b4, h4, a4 = lad[("4", "Black")], lad[("4", "Hispanic")], lad[("4", "Asian")]
    pb, ph, pa = prow[("3", "Black")], prow[("3", "Hispanic")], prow[("3", "Asian")]

    def price_txt(r: dict, name: str) -> str:
        if sig(r["ci_low"], r["ci_high"]):
            word = "more" if r["coef"] > 0 else "less"
            return f"{name} borrowers pay {abs(r['coef']):.1f} bps {word} ({_ci(r['ci_low'], r['ci_high'], 1, ' bps')})"
        return f"{name} borrowers pay about the same ({r['coef']:+.1f} bps, {_ci(r['ci_low'], r['ci_high'], 1, ' bps')})"

    top_block_b = max(oax["Black"]["blocks"].items(), key=lambda kv: kv[1])
    top_block_h = max(oax["Hispanic"]["blocks"].items(), key=lambda kv: kv[1])
    h80, h0 = hood["5 80%+"], hood["1 <10%"]
    hood_sig = h80["ci_low"] is not None and sig(h80["ci_low"], h80["ci_high"])
    s44 = scen["DTI cap 44%"]
    s44g = {r["applicant_group"]: r for r in s44["by_group"]}
    s95 = {r["applicant_group"]: r for r in scen["LTV cap 95%"]["by_group"]}
    any_below = results["groups"]["any_below_four_fifths"]
    below_after = [x for x in config.GROUPS if s44g[x]["air_after"] < config.FOUR_FIFTHS]

    findings = [
        (f"**{b['core_applications']:,} home-purchase applications reached a credit decision in 2025** in the core "
         f"sample (first-lien, owner-occupied, site-built 1-4 unit homes; {_p(b['core_share'], 0)} of all "
         f"{b['all_applications']:,} decided home-purchase applications reported under HMDA). {_p(1 - b['denial_rate'])} "
         f"were approved and {_p(b['denial_rate'])} denied; {b['originated']:,} loans closed for "
         f"{_usd(b['originated_volume'])}."),
        (f"**Black applicants were denied {bl['denial_ratio']:.1f} times as often as White applicants** "
         f"({_p(bl['denial_rate'])} against {_p(w['denial_rate'])}); Hispanic applicants {_p(hi['denial_rate'])} "
         f"({hi['denial_ratio']:.1f}x) and Asian applicants {_p(asn['denial_rate'])} ({asn['denial_ratio']:.1f}x). "
         + ("Every group still passes the four-fifths screen on approval rates (lowest ratio "
            f"{lowest_air['approval_air']:.2f}, {lowest_air['applicant_group']}), because approval rates near 90% "
            "make large denial gaps look small as approval ratios. Denial-rate ratios are the better screen here."
            if not any_below else
            f"The {lowest_air['applicant_group']} approval-rate ratio ({lowest_air['approval_air']:.2f}) is below the "
            "four-fifths screen.")),
        (f"**Debt-to-income above 49% is close to an automatic denial for conventional loans.** The conventional "
         f"denial rate is {_p(cliff['conventional_at_49'])} at a reported DTI of 49% and {_p(cliff['conventional_50_60'])} "
         f"at 50-60% ({_p(cliff['conventional_over_60'], 0)} above 60%), matching Fannie Mae's 50% maximum for "
         f"automated underwriting; DTI is cited in {_p(cliff['conventional_50_60_share_citing_dti'], 0)} of those "
         f"denials. "
         + (f"FHA has no cliff at 50% ({_p(cliff['fha_at_49'])} at 49%, {_p(cliff['fha_50_60'])} at 50-60%). "
            if cliff["fha_50_60"] - cliff["fha_at_49"] < 0.05 else
            f"FHA rises less ({_p(cliff['fha_at_49'])} at 49%, {_p(cliff['fha_50_60'])} at 50-60%). ")
         + f"{_p(bl['share_dti_50_plus'], 0)} of Black and {_p(hi['share_dti_50_plus'], 0)} of Hispanic applicants report "
         f"DTI of 50% or more, against {_p(w['share_dti_50_plus'], 0)} of White applicants."),
        (f"**Underwriting factors explain {share_word(expl['Black'])} of the Black-White gap"
         + (" and less of the Hispanic and Asian gaps.** " if expl["Hispanic"] < expl["Black"] and expl["Asian"] < expl["Black"]
            else ".** ")
         + f"Adding DTI, "
         f"loan-to-value, income, loan size, loan type, age, sex and neighbourhood income cuts the Black-White gap from "
         f"{_pp(lad[('1', 'Black')]['coef'])} to {_pp(lad[('2', 'Black')]['coef'])} ({_p(expl['Black'], 0)} explained) "
         f"and the Hispanic gap from {_pp(lad[('1', 'Hispanic')]['coef'])} to {_pp(lad[('2', 'Hispanic')]['coef'])}. "
         f"Comparing applicants at the same lender in the same county leaves {_pp(b4['coef'])} for Black applicants "
         f"({_ci(b4['ci_low'], b4['ci_high'])}), {_pp(h4['coef'])} for Hispanic and {_pp(a4['coef'])} for Asian "
         f"applicants. A logit model on {logit['Black']['n']:,} applications gives the same picture (Black marginal "
         f"effect {_pp(logit['Black']['ame'])}, odds ratio {logit['Black']['odds_ratio']:.2f})."),
        (f"**The largest explained part is {top_block_b[0].lower()}.** In the Oaxaca-Blinder decomposition it accounts "
         f"for {_pp(top_block_b[1])} of the {_pp(oax['Black']['raw_gap'])} Black-White gap; "
         f"{top_block_h[0].lower()} accounts for {_pp(top_block_h[1])} of the {_pp(oax['Hispanic']['raw_gap'])} "
         f"Hispanic-White gap."),
        (f"**Credit history is the factor HMDA cannot control for.** It is cited in {_p(reasons['credit_history']['Black'], 0)} "
         f"of denials of Black applicants and {_p(reasons['credit_history']['White'], 0)} of denials of White applicants. "
         "The public data has no credit scores, so part of the unexplained gap may be credit differences; a lender "
         "can close this question with its own score data, the public file cannot."),
        (f"**Pricing: at the same lender in the same state, {price_txt(ph, 'Hispanic')}** than comparable White "
         f"borrowers on {pr['loans']:,} originated conventional 30-year fixed loans (rate spread over the average "
         f"prime offer rate, controlling for points paid). {price_txt(pb, 'Black')}; {price_txt(pa, 'Asian')}."),
        (f"**Neighbourhood: applications in tracts that are 80%+ minority are denied at {_p(h80['raw_denial_rate'])}** "
         f"against {_p(h0['raw_denial_rate'])} in tracts under 10% minority. "
         + (f"After applicant controls and lender x state effects the difference is {_pp(h80['coef'])} "
            f"({_ci(h80['ci_low'], h80['ci_high'])}): most of the raw gap comes from who applies there, and a "
            "small part is tied to the location."
            if hood_sig and h80["coef"] > 0 and h80["coef"] < 0.25 * h80["raw_gap"] else
            f"After applicant controls and lender x state effects the difference is {_pp(h80['coef'])} "
            f"({_ci(h80['ci_low'], h80['ci_high'])}), so the location itself still matters."
            if hood_sig and h80["coef"] > 0 else
            f"After applicant controls and lender x state effects the difference is {_pp(h80['coef'])} "
            f"({_ci(h80['ci_low'], h80['ci_high'])}): the raw neighbourhood gap comes from who applies there, "
            "not from the location.")),
        (f"**Lender screen: {ls['black_gap_above_zero']} of the {ls['lenders']} largest lenders show a Black-White "
         f"denial gap whose 95% interval is above zero after controls and county effects**, and "
         f"{ls['hispanic_gap_above_zero']} show one for Hispanic applicants (median adjusted gaps "
         f"{_pp(ls['median_adj_gap_black'])} and {_pp(ls['median_adj_gap_hispanic'])}). These are screening results "
         f"that point to files to review, not findings."),
        (f"**A 44% DTI cap would remove {s44['total_approvals_lost']:,} approvals ({_p(s44['total_share_lost'])}) and "
         f"{_usd(s44['volume_lost'])} of loans,** falling on {_p(s44g['Black']['share_lost'])} of Black and "
         f"{_p(s44g['Hispanic']['share_lost'])} of Hispanic approvals against {_p(s44g['White']['share_lost'])} of White "
         f"approvals. The Black approval-rate ratio would fall from {s44g['Black']['air']:.3f} to "
         f"{s44g['Black']['air_after']:.3f}"
         + (f", and {join(below_after)} applicants would fall below the four-fifths screen." if below_after else
            ", still above the four-fifths screen.")),
    ]
    recs = [
        ("Track denial-rate ratios and adjusted gaps every quarter next to the four-fifths approval ratio, which "
         f"passes for every group even though Black applicants are denied {bl['denial_ratio']:.1f} times as often."
         if not any_below else
         "Track denial-rate ratios and adjusted gaps every quarter alongside the four-fifths approval ratio."),
        f"Before any guideline change, run the Excel simulator: a 44% DTI cap removes {_p(s44g['Black']['share_lost'])} "
        f"of Black approvals and an LTV cap at 95% removes {_p(s95['Black']['share_lost'])}, against "
        f"{_p(s44g['White']['share_lost'])} and {_p(s95['White']['share_lost'])} for White applicants. Document a "
        "business need and a less discriminatory alternative for any cap that lowers a group's ratio.",
        "Offer debt-payoff and loan-size counselling at application to applicants whose DTI is just above 49%, "
        "where conventional denial rates jump; FHA is an alternative product for many of them.",
        "Rerun the gap ladder on internal data with credit scores and full DTI detail. The remaining gap after "
        "scores is the figure regulators examine; the public data stops one step short of it.",
        "Review pricing exceptions and lender credits for Hispanic borrowers, where the rate-spread gap remains "
        "within lender and state.",
        "Use the lender screen as a peer benchmark: lenders with an interval above zero should sample denied "
        "files of comparable Black, Hispanic and White applicants for review.",
    ]
    pbi = results.get("powerbi", {})
    readme = f"""# Mortgage Approval and Fair-Lending Analysis (HMDA 2025)

**Who gets turned down for a home-purchase mortgage, why, and how much of the gap between groups is left after
underwriting factors are accounted for?** This project runs the screens a bank's fair-lending team runs on its
own HMDA data, on every 2025 U.S. home-purchase application that reached a decision ({b['all_applications']:,}
records; {b['core_applications']:,} applications to {b['lenders']:,} lenders in the core sample). It ends with an Excel simulator that tests a
credit-policy change for disparate impact before it goes live, and a Power BI report.

**Tools:** SQL (DuckDB: typed staging of 99 text columns, quality rules, grouping sets, unnest of denial
reasons, lender, state, county and tract views) · Python (pandas, NumPy, statsmodels, SciPy) · Statistics
(Wilson intervals, linear probability models with absorbed lender x county fixed effects and errors
clustered by lender, logit marginal effects with delta-method intervals, Oaxaca-Blinder decomposition) ·
Excel (policy simulator with formulas, data validation and four-fifths flags) · Power BI (TMDL model,
DAX, four-page PBIR report)

![Denial gap as controls are added](reports/figures/02_denial_gap_ladder.png)

## Findings

""" + "\n".join(f"{i}. {t}" for i, t in enumerate(findings, 1)) + """

![Denial by debt-to-income](reports/figures/03_denial_by_dti.png)

![Gap decomposition](reports/figures/05_gap_decomposition.png)

## Recommendations for a lender's fair-lending team

""" + "\n".join(f"{i}. {t}" for i, t in enumerate(recs, 1)) + f"""

## Deliverables

| Deliverable | Where |
|---|---|
| Power BI project: TMDL model ({pbi.get('tables', 9)} tables, {pbi.get('relationships', 5)} relationships, {pbi.get('measures', 23)} DAX measures), 4 report pages | `dashboards/powerbi/MortgageFairLending.pbip` |
| CSV extracts used by Power BI | `dashboards/powerbi/data/` |
| Excel underwriting policy and fair-lending simulator | `excel/underwriting_policy_fair_lending_model.xlsx` |
| Analysis notebook with outputs | `notebooks/hmda_fair_lending.ipynb` |
| One-page memo | `reports/memo.md` |
| SQL: load, typing, {results['quality']['rules']} quality rules, funnel, group rates, DTI profile, denial reasons, lenders, geography, policy grid | `sql/` |
| Result tables and figures | `reports/tables/`, `reports/figures/` |

![Power BI fair-lending page preview](dashboards/powerbi/report_preview.png)

The Power BI project was generated from code and its report files validate against Microsoft's published
PBIR JSON schemas. Power BI Desktop runs on Windows only, so the preview above is a Python rendering of the
Fair-lending screen page from the same CSVs. To open the real report on Windows: open
`MortgageFairLending.pbip` in Power BI Desktop, set the `DataFolder` parameter (Transform data > Edit
parameters) to the full path of `dashboards/powerbi/data/`, and click Refresh.

## How it works

1. **Warehouse** (`sql/01-03`): DuckDB loads the {rc['lar_raw']:,}-row file as text, types every field
   ('NA' and 'Exempt' become NULL), labels applicant groups, bands DTI, LTV, income and tract
   characteristics, and runs {results['quality']['rules']} quality rules
   ([`docs/data_quality_log.md`](docs/data_quality_log.md)).
2. **Views** (`sql/04-14`): decision funnel, rates by group and loan type, denial by exact DTI, denial reasons,
   lender benchmark, state, county and tract views, the Power BI fact table and the Excel policy grid.
3. **Gap ladder** (`src/fairlending.py`, `src/stats.py`): denial on group indicators, then underwriting controls,
   then lender x state and lender x county fixed effects, on the {mf['applications']:,} applications with every
   control ({_p(mf['share_of_core'], 0)} of the core sample). Errors clustered by lender.
4. **Checks on the gap**: logit average marginal effects on a {logit['Black']['n']:,}-row random sample;
   Oaxaca-Blinder decomposition; pricing gaps on originated conventional 30-year fixed loans; neighbourhood
   gaps by tract minority share; within-lender gaps for the {ls['lenders']} largest lenders.
5. **Business tools**: Excel simulator over the group x DTI x LTV grid (Python twin in
   `fairlending.simulate_policy` gives the same numbers); Power BI model and report from `src/powerbi.py`.

Details: [`docs/methodology.md`](docs/methodology.md) · data dictionary: [`docs/data_dictionary.md`](docs/data_dictionary.md)

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make all        # download (1.7 GB), build warehouse, statistics, notebook, tests (about 10 minutes)
```

## Project structure

```
├── data/                 raw/ and processed/ (git-ignored); README with sources
├── sql/                  DuckDB SQL: load, typing, quality rules, analysis views, Power BI and Excel extracts
├── src/                  pipeline: data, statistics, fair-lending screens, figures, Excel, Power BI, report
├── notebooks/            executed analysis notebook
├── excel/                underwriting policy and fair-lending simulator
├── dashboards/powerbi/   .pbip project (SemanticModel + Report), CSV extracts, preview
├── reports/              results.json, memo, figures, tables
├── docs/                 methodology, data dictionary, data quality log
└── tests/                pytest suite
```

## Data

Home Mortgage Disclosure Act (HMDA) loan application register, 2025 filing year, published by the CFPB and
FFIEC. Downloaded from the HMDA Data Browser API (nationwide, loan purpose = home purchase, action taken =
originated, approved not accepted or denied): [ffiec.cfpb.gov/data-browser](https://ffiec.cfpb.gov/data-browser/).
Lender names come from the HMDA filers list for 2025 and county names from the Census Bureau's 2020 county
codes. No account is needed. Raw files are not stored in this repository.

## Assumptions and limits

* HMDA has no credit scores, assets or employment detail, and reports DTI in bands outside 36-49%. Adjusted gaps
  are screening statistics. They show where to look, not that discrimination occurred.
* {_p(1 - mf['share_of_core'], 0)} of core applications miss a control (mostly DTI or LTV) and are left out of the
  regressions; their denial rates are higher (see `reports/tables/model_frame_exclusions.csv`), so the regression
  sample has a lower denial rate ({_p(mf['denial_rate'])}) than the core sample.
* Denied preapproval requests are reported under a separate action code and are not in this data; applications
  that went through preapproval show no denials and the preapproval flag is not used as a control.
* Applicant group follows HMDA's derived ethnicity and race fields: Hispanic applicants of any race form one
  group; the others are non-Hispanic. Joint applications with mixed groups and unreported race are shown but not
  compared.
* The Excel simulator gives the first-order effect of a cap: approved applicants above it are lost. Some would
  restructure the loan to fit, so losses are an upper bound. The revenue rate ({config.GAIN_ON_SALE_BPS} bps) is an
  assumption to replace.
* Rate spread is measured against the average prime offer rate on the lock date, which HMDA does not publish, so
  the pricing comparison cannot control for the timing of the rate lock beyond the lender x state effect.
"""
    (config.ROOT / "README.md").write_text(readme)
    memo = ("# Memo: fair-lending screen of 2025 home-purchase mortgage decisions\n\n**To:** Chief Compliance Officer "
            f"· **Data:** HMDA 2025, {b['core_applications']:,} decided home-purchase applications (core sample)\n\n"
            "**What we found**\n\n" + "\n".join(f"- {t}" for t in findings) + "\n\n**What to do**\n\n"
            + "\n".join(f"{i}. {t}" for i, t in enumerate(recs, 1))
            + "\n\n**Caveats:** no credit scores in HMDA; adjusted gaps are screens, not findings; policy-cap losses are "
              "upper bounds; the revenue rate is an assumption.\n")
    (config.REPORTS / "memo.md").write_text(memo)
