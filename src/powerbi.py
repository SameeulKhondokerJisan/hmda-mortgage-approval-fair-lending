"""Power BI deliverable: CSV extracts + a generated Power BI project (.pbip, TMDL model + PBIR report).

Writes dashboards/powerbi/data/*.csv, dashboards/powerbi/MortgageFairLending.pbip and a Python-rendered
preview of the Fair-lending screen page for the README.
"""
from __future__ import annotations

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from src import config  # noqa: E402
from src.pbip import Measure, Page, Relationship, Table, Visual, validate, write_project  # noqa: E402

SCHEMA_ROOT = config.ROOT.parent / "_tools" / "json-schemas" / "fabric"


def export(cube, income_tract, dti, reasons, ladder, price, screen, counties) -> dict:
    d = config.POWERBI_DATA
    d.mkdir(parents=True, exist_ok=True)
    cube.to_csv(d / "fact_applications.csv", index=False)
    income_tract.to_csv(d / "income_tract.csv", index=False)
    dti[["loan_type", "dti_value", "dti_band", "applications", "denial_rate", "share_of_denials_citing_dti"]].to_csv(
        d / "dti_profile.csv", index=False)
    reasons[["applicant_group", "reason", "denied_citing", "denied_apps", "share_of_denials"]].to_csv(
        d / "denial_reasons.csv", index=False)
    lad = ladder.rename(columns={"group": "applicant_group"}).copy()
    lad["gap_pp"], lad["ci_low_pp"], lad["ci_high_pp"] = lad.coef * 100, lad.ci_low * 100, lad.ci_high * 100
    lad[["spec", "applicant_group", "gap_pp", "ci_low_pp", "ci_high_pp", "p"]].to_csv(d / "gap_ladder.csv", index=False)
    pr = price.rename(columns={"group": "applicant_group", "coef": "gap_bps", "ci_low": "ci_low_bps",
                               "ci_high": "ci_high_bps"})
    pr[["spec", "applicant_group", "gap_bps", "ci_low_bps", "ci_high_bps", "p"]].to_csv(d / "pricing_gaps.csv",
                                                                                        index=False)
    sc = screen.copy()
    for c in [c for c in sc.columns if c.startswith(("raw_gap", "adj_gap", "ci_low", "ci_high"))]:
        sc[c] = sc[c] * 100
    sc.drop(columns=["lei"]).to_csv(d / "lender_screen.csv", index=False)
    counties.drop(columns=["county_fips"]).to_csv(d / "county_rates.csv", index=False)
    pd.DataFrame({"applicant_group": config.GROUP_ORDER, "group_order": range(1, len(config.GROUP_ORDER) + 1),
                  "is_reference": [int(g == config.REFERENCE_GROUP) for g in config.GROUP_ORDER]}).to_csv(
        d / "dim_group.csv", index=False)
    return build_project()


def build_project() -> dict:
    d = config.POWERBI_DATA
    F, IT, DP, DR, GL, PG, LS, CR = ("fact_applications", "income_tract", "dti_profile", "denial_reasons",
                                     "gap_ladder", "pricing_gaps", "lender_screen", "county_rates")
    core = [
        Measure("Applications", f"SUM({F}[applications])", "#,0", "Volume"),
        Measure("Approved", f"SUM({F}[approved])", "#,0", "Volume"),
        Measure("Denied", f"SUM({F}[denied])", "#,0", "Volume"),
        Measure("Originated", f"SUM({F}[originated])", "#,0", "Volume"),
        Measure("Originated volume ($)", f"SUM({F}[originated_volume])", "\\$#,0", "Volume"),
        Measure("Approval rate", "DIVIDE([Approved], [Applications])", "0.0%", "Rates"),
        Measure("Denial rate", "DIVIDE([Denied], [Applications])", "0.0%", "Rates"),
        Measure("White approval rate", "CALCULATE([Approval rate], dim_group[applicant_group] = \"White\")", "0.0%",
                "Fair lending"),
        Measure("White denial rate", "CALCULATE([Denial rate], dim_group[applicant_group] = \"White\")", "0.0%",
                "Fair lending"),
        Measure("Approval AIR", "DIVIDE([Approval rate], [White approval rate])", "0.000", "Fair lending"),
        Measure("Denial-rate ratio", "DIVIDE([Denial rate], [White denial rate])", "0.00", "Fair lending"),
        Measure("Denial gap vs White (pp)", "([Denial rate] - [White denial rate]) * 100", "0.0", "Fair lending"),
        Measure("Below four-fifths", f"IF([Approval AIR] < {config.FOUR_FIFTHS}, \"Below 0.80\", \"Passes\")", None,
                "Fair lending"),
        Measure("Share with DTI above 49%",
                f"DIVIDE(CALCULATE([Applications], {F}[dti_band] IN {{\"7 50-60%\", \"8 >60%\"}}), [Applications])",
                "0.0%", "Underwriting"),
    ]
    tables = [
        Table(F, d / f"{F}.csv", core, formats={"originated_volume": "\\$#,0"}),
        Table(IT, d / f"{IT}.csv", [Measure("Denial rate (income and tract)",
                                            f"DIVIDE(SUM({IT}[denied]), SUM({IT}[applications]))", "0.0%")]),
        Table(DP, d / f"{DP}.csv", [Measure("Denial rate by DTI", f"DIVIDE(SUMX({DP}, {DP}[applications] * "
                                                                  f"{DP}[denial_rate]), SUM({DP}[applications]))",
                                            "0.0%")],
              formats={"denial_rate": "0.0%", "share_of_denials_citing_dti": "0.0%"}),
        Table(DR, d / f"{DR}.csv", [Measure("Share of denials citing reason",
                                            f"DIVIDE(SUM({DR}[denied_citing]), SUM({DR}[denied_apps]))", "0.0%")],
              formats={"share_of_denials": "0.0%"}),
        Table(GL, d / f"{GL}.csv", [Measure("Denial gap (pp)", f"AVERAGE({GL}[gap_pp])", "0.0")],
              formats={"gap_pp": "0.0", "ci_low_pp": "0.0", "ci_high_pp": "0.0", "p": "0.0000"}),
        Table(PG, d / f"{PG}.csv", [Measure("Rate spread gap (bps)", f"AVERAGE({PG}[gap_bps])", "0.0")],
              formats={"gap_bps": "0.0", "ci_low_bps": "0.0", "ci_high_bps": "0.0", "p": "0.0000"}),
        Table(LS, d / f"{LS}.csv", [
            Measure("Lenders screened", f"COUNTROWS({LS})", "#,0"),
            Measure("Lenders with an adjusted gap above zero",
                    f"COUNTROWS(FILTER({LS}, {LS}[ci_low_black] > 0 || {LS}[ci_low_hispanic] > 0))", "#,0"),
            Measure("Adjusted Black gap (pp)", f"AVERAGE({LS}[adj_gap_black])", "0.0")],
              formats={"denial_rate": "0.0%"}),
        Table(CR, d / f"{CR}.csv", formats={c: "0.0%" for c in ("denial_rate", "denial_rate_white", "denial_rate_black",
                                                               "denial_rate_hispanic")}),
        Table("dim_group", d / "dim_group.csv", key="applicant_group"),
    ]
    rels = [Relationship(F, "applicant_group", "dim_group", "applicant_group"),
            Relationship(IT, "applicant_group", "dim_group", "applicant_group"),
            Relationship(DR, "applicant_group", "dim_group", "applicant_group"),
            Relationship(GL, "applicant_group", "dim_group", "applicant_group"),
            Relationship(PG, "applicant_group", "dim_group", "applicant_group")]
    m = lambda t, n: ("measure", t, n)  # noqa: E731
    col = lambda t, n: ("column", t, n)  # noqa: E731

    def cards(items):
        return [Visual("card", 10 + i * 318, 10, 306, 90, {"Values": [c]}) for i, c in enumerate(items)]

    overview = Page("Market overview", cards([m(F, "Applications"), m(F, "Approval rate"), m(F, "Denial rate"),
                                              m(F, "Originated volume ($)")]) + [
        Visual("clusteredColumnChart", 10, 110, 400, 290, {"Category": [col(F, "loan_type")],
                                                           "Y": [m(F, "Denial rate")]}, "Denial rate by loan type"),
        Visual("clusteredBarChart", 420, 110, 420, 290, {"Category": [col("dim_group", "applicant_group")],
                                                         "Y": [m(F, "Applications")]}, "Applications by applicant group"),
        Visual("clusteredBarChart", 850, 110, 420, 600, {"Category": [col(F, "state_code")],
                                                         "Y": [m(F, "Denial rate")]}, "Denial rate by state"),
        Visual("tableEx", 10, 410, 830, 300, {"Values": [col(CR, c) for c in ("county", "applications", "denial_rate",
                                                                             "denial_rate_white", "denial_rate_black",
                                                                             "denial_rate_hispanic")]},
               f"Counties with {config.MIN_COUNTY_APPS}+ applications"),
    ])
    drivers = Page("Underwriting drivers", cards([m(F, "Share with DTI above 49%"), m(F, "Approved"), m(F, "Denied"),
                                                  m(F, "Originated")]) + [
        Visual("lineChart", 10, 110, 630, 290, {"Category": [col(DP, "dti_value")], "Series": [col(DP, "loan_type")],
                                                "Y": [m(DP, "Denial rate by DTI")]},
               "Denial rate by debt-to-income ratio (36-49% exact, others banded)"),
        Visual("clusteredColumnChart", 650, 110, 620, 290, {"Category": [col(F, "ltv_band")],
                                                            "Y": [m(F, "Denial rate")]}, "Denial rate by loan-to-value band"),
        Visual("pivotTable", 10, 410, 630, 300, {"Rows": [col(F, "dti_band")], "Columns": [col(F, "ltv_band")],
                                                 "Values": [m(F, "Denial rate")]}, "Denial rate: DTI band x LTV band"),
        Visual("clusteredBarChart", 650, 410, 620, 300, {"Category": [col(DR, "reason")],
                                                         "Series": [col("dim_group", "applicant_group")],
                                                         "Y": [m(DR, "Share of denials citing reason")]},
               "Denial reasons by applicant group"),
    ])
    screen_page = Page("Fair-lending screen", [
        Visual("tableEx", 10, 10, 630, 300, {"Values": [col("dim_group", "applicant_group"), m(F, "Applications"),
                                                        m(F, "Approval rate"), m(F, "Approval AIR"),
                                                        m(F, "Below four-fifths"), m(F, "Denial rate"),
                                                        m(F, "Denial-rate ratio")]},
               "Approval and denial rates against White applicants"),
        Visual("clusteredColumnChart", 650, 10, 620, 300, {"Category": [col(GL, "spec")],
                                                           "Series": [col("dim_group", "applicant_group")],
                                                           "Y": [m(GL, "Denial gap (pp)")]},
               "Denial gap vs White as controls are added (pp)"),
        Visual("pivotTable", 10, 320, 630, 390, {"Rows": [col(IT, "tract_minority_band")],
                                                 "Columns": [col(IT, "income_band")],
                                                 "Values": [m(IT, "Denial rate (income and tract)")]},
               "Denial rate: tract minority share x applicant income band"),
        Visual("clusteredColumnChart", 650, 320, 620, 390, {"Category": [col(PG, "spec")],
                                                            "Series": [col("dim_group", "applicant_group")],
                                                            "Y": [m(PG, "Rate spread gap (bps)")]},
               "Rate spread gap vs White borrowers, conventional 30-year fixed (bps)"),
    ])
    lenders = Page("Lender screen", cards([m(LS, "Lenders screened"), m(LS, "Lenders with an adjusted gap above zero"),
                                           m(LS, "Adjusted Black gap (pp)")]) + [
        Visual("clusteredBarChart", 10, 110, 560, 600, {"Category": [col(LS, "lender_name")],
                                                        "Y": [m(LS, "Adjusted Black gap (pp)")]},
               "Adjusted Black-White denial gap within each lender (pp)"),
        Visual("tableEx", 580, 110, 690, 600, {"Values": [col(LS, c) for c in
                                                         ("lender_name", "applications", "denial_rate", "adj_gap_black",
                                                          "ci_low_black", "ci_high_black", "adj_gap_hispanic",
                                                          "screen")]}, "Lender screen (screening statistics)"),
    ])
    pbip = write_project(config.POWERBI_DIR, "MortgageFairLending", tables, rels, [overview, drivers, screen_page, lenders],
                         data_folder_hint="C:\\path\\to\\hmda-mortgage-approval-fair-lending\\dashboards\\powerbi\\data\\")
    problems = validate(config.POWERBI_DIR, SCHEMA_ROOT) if SCHEMA_ROOT.exists() else ["schemas not available"]
    render_preview()
    return {"pbip": str(pbip.relative_to(config.ROOT)), "schema_problems": problems,
            "measures": sum(len(t.measures) for t in tables), "tables": len(tables), "relationships": len(rels),
            "pages": 4}


def render_preview() -> None:
    """Python rendering of the Fair-lending screen page layout, for the README (not a Power BI screenshot)."""
    d = config.POWERBI_DATA
    f = pd.read_csv(d / "fact_applications.csv")
    lad = pd.read_csv(d / "gap_ladder.csv")
    it = pd.read_csv(d / "income_tract.csv")
    pg = pd.read_csv(d / "pricing_gaps.csv")
    g = f.groupby("applicant_group")[["applications", "approved", "denied"]].sum()
    g = g.reindex([x for x in config.GROUP_ORDER if x in g.index])
    g["approval_rate"], g["denial_rate"] = g.approved / g.applications, g.denied / g.applications
    w = g.loc[config.REFERENCE_GROUP]
    g["air"], g["ratio"] = g.approval_rate / w.approval_rate, g.denial_rate / w.denial_rate
    fig = plt.figure(figsize=(16, 9), facecolor="#f3f2f1")
    ax = fig.add_axes([0.02, 0.56, 0.46, 0.40]); ax.axis("off")
    ax.set_title("Approval and denial rates against White applicants", loc="left", fontsize=11)
    cells = [[i, f"{r.applications:,.0f}", f"{r.approval_rate * 100:.1f}%", f"{r.air:.3f}",
              "Below 0.80" if r.air < config.FOUR_FIFTHS else "Passes", f"{r.denial_rate * 100:.1f}%", f"{r.ratio:.2f}"]
             for i, r in g.iterrows()]
    t = ax.table(cellText=cells, colLabels=["Group", "Applications", "Approval rate", "Approval AIR", "Four-fifths",
                                            "Denial rate", "Denial-rate ratio"], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(9); t.scale(1, 1.7)
    ax = fig.add_axes([0.54, 0.58, 0.44, 0.36])
    specs = list(dict.fromkeys(lad.spec))
    groups = [x for x in ("Black", "Hispanic", "Asian", "Other minority") if x in set(lad.applicant_group)]
    colors = ["#118DFF", "#E66C37", "#12239E", "#6B007B"]
    for i, (grp, c) in enumerate(zip(groups, colors)):
        v = lad[lad.applicant_group == grp].set_index("spec").reindex(specs).gap_pp
        ax.bar(np.arange(len(specs)) + (i - 1.5) * 0.2, v, 0.2, color=c, label=grp)
    ax.set_xticks(range(len(specs)), [s[2:] for s in specs], fontsize=8)
    ax.axhline(0, color="black", lw=0.6); ax.legend(fontsize=8, frameon=False, ncol=4)
    ax.set_title("Denial gap vs White as controls are added (pp)", loc="left", fontsize=11)
    piv = it.groupby(["tract_minority_band", "income_band"])[["denied", "applications"]].sum()
    piv = (piv.denied / piv.applications).unstack() * 100
    piv = piv.drop(columns=[c for c in piv.columns if "Missing" in c]).drop(index=[r for r in piv.index if "Unknown" in r])
    ax = fig.add_axes([0.04, 0.06, 0.42, 0.38]); ax.axis("off")
    ax.set_title("Denial rate (%): tract minority share x applicant income band", loc="left", fontsize=11)
    t = ax.table(cellText=[[f"{v:.1f}" for v in row] for row in piv.to_numpy()], rowLabels=[r[2:] for r in piv.index],
                 colLabels=[c[2:] for c in piv.columns], loc="center", cellLoc="center")
    t.auto_set_font_size(False); t.set_fontsize(8); t.scale(1, 1.8)
    ax = fig.add_axes([0.54, 0.08, 0.44, 0.36])
    pspecs = list(dict.fromkeys(pg.spec))
    for i, (grp, c) in enumerate(zip(["Black", "Hispanic", "Asian"], colors)):
        v = pg[pg.applicant_group == grp].set_index("spec").reindex(pspecs).gap_bps
        ax.bar(np.arange(len(pspecs)) + (i - 1) * 0.25, v, 0.25, color=c, label=grp)
    ax.set_xticks(range(len(pspecs)), [s[2:] for s in pspecs], fontsize=8)
    ax.axhline(0, color="black", lw=0.6); ax.legend(fontsize=8, frameon=False, ncol=3)
    ax.set_title("Rate spread gap vs White borrowers, conventional 30-year fixed (bps)", loc="left", fontsize=11)
    for a in fig.axes:
        a.spines[["top", "right"]].set_visible(False)
    fig.text(0.99, 0.005, "Python preview of the Power BI 'Fair-lending screen' page layout (same data and measures)",
             ha="right", fontsize=8, color="#605e5c")
    fig.savefig(config.POWERBI_DIR / "report_preview.png", dpi=110)
    plt.close(fig)
