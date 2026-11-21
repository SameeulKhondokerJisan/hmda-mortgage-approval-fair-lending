"""Create notebooks/hmda_fair_lending.ipynb (executed by `make notebook`)."""
import nbformat as nbf

from src import config

CELLS = [
    ("md", "# HMDA 2025: mortgage approval and fair-lending screens\nWalk-through of the analysis behind the README. "
           "SQL runs live against the DuckDB warehouse built by `src/run_pipeline.py`; regression results are read "
           "from `reports/` (the fixed-effects models on 2.5 million rows take a few minutes)."),
    ("code", "import os, sys, json, pathlib\nROOT = pathlib.Path.cwd().parent if pathlib.Path.cwd().name == 'notebooks' "
             "else pathlib.Path.cwd()\nos.chdir(ROOT); sys.path.insert(0, str(ROOT))\nimport pandas as pd\n"
             "from IPython.display import Image, Markdown, display\nfrom src import config, data, fairlending\n"
             "pd.set_option('display.float_format', lambda x: f'{x:,.4f}')\npd.set_option('display.width', 160)\n"
             "results = json.loads(config.RESULTS_JSON.read_text())\nT = lambda name: pd.read_csv(f'reports/tables/{name}.csv')"),
    ("md", "## 1. Data quality and scope\nHard rules stop the pipeline. The core sample keeps first-lien, owner-occupied, "
           "site-built 1-4 unit home-purchase applications with a credit decision."),
    ("code", "display(T('quality_checks'))\ndata.row_counts()"),
    ("code", "data.query('04_funnel.sql')"),
    ("md", "## 2. Denial rates by applicant group\nWilson 95% intervals; approval-rate adverse impact ratio (AIR) and "
           "denial-rate ratio against White applicants."),
    ("code", "cols = ['applicant_group', 'applications', 'approval_rate', 'denial_rate', 'denial_ci_low', 'denial_ci_high', "
             "'approval_air', 'denial_ratio', 'share_dti_50_plus', 'share_ltv_over_95']\ndisplay(T('rates_by_group')[cols])\n"
             "display(Image(filename='reports/figures/01_denial_rate_by_group.png'))"),
    ("md", "## 3. Underwriting: the debt-to-income cliff\nHMDA reports DTI from 36% to 49% as exact values and other "
           "values in bands (`sql/06_dti_profile.sql`)."),
    ("code", "dti = data.query('06_dti_profile.sql')\ndisplay(dti[dti.loan_type == 'Conventional'])\n"
             "display(Image(filename='reports/figures/03_denial_by_dti.png'))"),
    ("md", "Denial reasons (up to four per application), from an `unnest` over the four reason columns."),
    ("code", "r = T('denial_reasons')\ndisplay(r.pivot(index='reason', columns='applicant_group', values='share_of_denials')"
             "[['White', 'Black', 'Hispanic', 'Asian']].sort_values('White', ascending=False))\n"
             "display(Image(filename='reports/figures/04_denial_reasons.png'))"),
    ("md", "## 4. The gap ladder\nLinear probability model of denial. Specification 1: group indicators only. 2: plus "
           "DTI band, LTV band, log income, log loan amount, log property value, conforming flag, loan type, age, "
           "sex, application channel and tract income band. 3 and 4: plus absorbed lender x state or lender x county "
           "fixed effects. Errors clustered by lender."),
    ("code", "lad = T('denial_gap_ladder')\nlad.assign(gap_pp=lad.coef * 100, ci_low_pp=lad.ci_low * 100, "
             "ci_high_pp=lad.ci_high * 100).pivot(index='spec', columns='group', values='gap_pp').round(2)"),
    ("code", "display(pd.DataFrame(results['gap_ladder']['fits']).T)\n"
             "display(Image(filename='reports/figures/02_denial_gap_ladder.png'))"),
    ("md", "Robustness: logit with the same controls and state dummies on a random sample; average marginal effects with "
           "delta-method intervals."),
    ("code", "T('logit_marginal_effects')"),
    ("md", "## 5. Oaxaca-Blinder decomposition\nPooled coefficients with a group indicator, so explained + unexplained "
           "equals the raw gap."),
    ("code", "display(T('oaxaca_blinder'))\ndisplay(Image(filename='reports/figures/05_gap_decomposition.png'))"),
    ("md", "## 6. Pricing and neighbourhoods"),
    ("code", "p = T('pricing_gaps')\ndisplay(p.pivot(index='spec', columns='group', values='coef').round(1))\n"
             "display(Image(filename='reports/figures/07_pricing_gaps.png'))"),
    ("code", "display(T('neighbourhood_gaps'))\ndisplay(Image(filename='reports/figures/06_denial_by_neighbourhood.png'))"),
    ("md", "## 7. Lender screen\nWithin each large lender: controls plus county fixed effects, errors clustered by county. "
           "Screening statistics, not findings."),
    ("code", "s = T('lender_screen')\ndisplay(s[['lender_name', 'applications', 'denial_rate', 'raw_gap_black', 'adj_gap_black', "
             "'ci_low_black', 'ci_high_black', 'adj_gap_hispanic', 'screen']])\n"
             "display(Image(filename='reports/figures/08_lender_screen.png'))"),
    ("md", "## 8. Policy simulator\nWhat a 44% DTI cap would do to approvals by group (same logic as the Excel model)."),
    ("code", "grid = data.query('13_policy_grid.sql')\nfairlending.simulate_policy(grid, dti_max=5)[['applicant_group', "
             "'approved', 'approved_after', 'share_lost', 'air', 'air_after', 'volume_lost']]"),
    ("md", "## 9. Memo"),
    ("code", "display(Markdown(open('reports/memo.md').read()))"),
]


def main() -> None:
    nb = nbf.v4.new_notebook()
    nb.cells = [nbf.v4.new_markdown_cell(s) if k == "md" else nbf.v4.new_code_cell(s) for k, s in CELLS]
    nb.metadata["kernelspec"] = {"display_name": "Python 3", "language": "python", "name": "python3"}
    (config.ROOT / "notebooks").mkdir(exist_ok=True)
    nbf.write(nb, config.ROOT / "notebooks" / "hmda_fair_lending.ipynb")


if __name__ == "__main__":
    main()
