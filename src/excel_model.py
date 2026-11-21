"""Build excel/underwriting_policy_fair_lending_model.xlsx.

A credit-policy simulator of the kind a fair-lending team runs before a guideline change: pick a
maximum debt-to-income and loan-to-value ratio, and the workbook shows how many approvals each applicant
group would lose, the change in approval-rate adverse impact ratios against the four-fifths screen, and
the loan volume and revenue at stake. Every calculated cell is a formula over the Grid sheet (counts from
the HMDA core sample). With no caps the workbook reproduces the pipeline's approval counts exactly
(checked by tests/test_excel.py after recalculation).

Colour code: blue = typed input or pasted data, black = formula, green = link to another sheet,
yellow fill = assumption to review.
"""
from __future__ import annotations

import pandas as pd
from openpyxl import Workbook
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.datavalidation import DataValidation

from src import config

ARIAL = "Arial"
BLUE, BLACK, GREEN, WHITE = "0000FF", "000000", "008000", "FFFFFF"
HEADER = PatternFill("solid", fgColor="1F3864")
YELLOW = PatternFill("solid", fgColor="FFFF00")
RED_FILL = PatternFill("solid", fgColor="F8CBAD")
THIN = Side(style="thin", color="BFBFBF")
BOX = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
USD = '"$"#,##0;("$"#,##0);"-"'
USDM = '"$"#,##0.0,,"M";("$"#,##0.0,,"M");"-"'
PCT = '0.0%;(0.0%);"-"'
PCT2 = '0.00%;(0.00%);"-"'
NUM = '#,##0;(#,##0);"-"'
RATIO = '0.000'
SRC = ("Source: HMDA 2025 loan application records (CFPB/FFIEC Data Browser), core sample: first-lien, "
       "owner-occupied, site-built 1-4 unit home purchase applications with a credit decision. Built by "
       "src/excel_model.py from reports/results.json.")
GROUPS = ["White", "Black", "Hispanic", "Asian", "Other minority"]
DTI_CAPS = [("No cap", 9), ("35%", 3), ("39%", 4), ("44%", 5), ("49%", 6), ("60%", 7)]
LTV_CAPS = [("No cap", 7), ("80%", 2), ("90%", 3), ("95%", 4), ("97%", 5)]


def _c(ws, ref, value, color=BLACK, fmt=None, bold=False, fill=None, note=None, italic=False, size=10):
    cell = ws[ref]
    cell.value = value
    cell.font = Font(name=ARIAL, color=color, bold=bold, italic=italic, size=size)
    if fmt:
        cell.number_format = fmt
    if fill:
        cell.fill = fill
    if note:
        cell.comment = Comment(note, "pipeline")
    return cell


def _head(ws, row, labels, col=1):
    for i, text in enumerate(labels):
        cell = ws.cell(row=row, column=col + i, value=text)
        cell.font = Font(name=ARIAL, color=WHITE, bold=True)
        cell.fill = HEADER
        cell.border = BOX
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def _widths(ws, widths: dict[str, float]) -> None:
    for col, w in widths.items():
        ws.column_dimensions[col].width = w


def build(results: dict, grid: pd.DataFrame, ladder: pd.DataFrame, screen: pd.DataFrame) -> str:
    wb = Workbook()
    # ------------------------------------------------------------------ README
    ws = wb.active
    ws.title = "README"
    _c(ws, "A1", "HMDA 2025: underwriting policy and fair-lending simulator", bold=True, size=14)
    _c(ws, "A2", "What a stricter debt-to-income or loan-to-value cap would do to approvals by applicant group",
       italic=True)
    lines = [
        "Purpose: test a proposed credit-policy change for disparate impact before it goes live, and size the "
        "loan volume it gives up.",
        "Inputs: choose a DTI cap and an LTV cap (yellow cells). 'No cap' reproduces 2025 decisions.",
        "Grid: 2025 applications, approvals and approved loan volume by applicant group, DTI band and LTV band "
        "(blue, from the HMDA core sample). Column J flags the rows that still pass the chosen caps.",
        "Summary: approvals and approval rates before and after the caps, the approval-rate adverse impact ratio "
        "(group approval rate / White approval rate) against the four-fifths screen, denial-rate ratios, and "
        "the volume and revenue lost.",
        "Gap results: denial gaps from the regressions in the Python pipeline, and the approval ratio they imply.",
        "Lender screen: within-lender adjusted gaps for the largest lenders (screening statistics).",
        "Method: a capped row loses only the applications that were approved; denied applications stay denied. "
        "This is the first-order effect of a tighter guideline; it ignores applicants who would restructure "
        "the loan to fit the cap.",
        "Limits: HMDA has no credit scores. Adjusted gaps are screens that point to files to review, not "
        "findings of discrimination. The four-fifths ratio comes from employment law and is a screening rule "
        "of thumb in lending, not a legal threshold.",
        "Colour code: blue = input or pasted data; black = formula; green = link to another sheet; yellow fill "
        "= assumption to review.",
        SRC,
    ]
    for i, text in enumerate(lines, start=4):
        _c(ws, f"A{i}", text)
    ws.column_dimensions["A"].width = 130

    # ------------------------------------------------------------------ Inputs
    inp = wb.create_sheet("Inputs")
    _c(inp, "A1", "Inputs", bold=True, size=14)
    _c(inp, "A2", "Edit the yellow cells; everything else recalculates.", italic=True)
    _head(inp, 4, ["Input", "Value", "Note"])
    _c(inp, "A5", "Maximum debt-to-income ratio")
    _c(inp, "B5", config.DEFAULT_DTI_CAP, BLUE, fill=YELLOW)
    _c(inp, "C5", "No cap, 35%, 39%, 44%, 49% or 60%. HMDA reports DTI in these steps above 35%.")
    _c(inp, "A6", "Maximum loan-to-value ratio")
    _c(inp, "B6", config.DEFAULT_LTV_CAP, BLUE, fill=YELLOW)
    _c(inp, "C6", "No cap, 80%, 90%, 95% or 97%.")
    _c(inp, "A7", "Applications with DTI or LTV not reported pass the cap?")
    _c(inp, "B7", "Yes", BLUE, fill=YELLOW)
    _c(inp, "C7", "Yes or No. Only matters when a cap is set.")
    _c(inp, "A8", "Revenue per originated dollar (basis points)")
    _c(inp, "B8", config.GAIN_ON_SALE_BPS, BLUE, "0", fill=YELLOW,
       note="Assumption: origination and gain-on-sale revenue per dollar lent. Replace with your own figure.")
    _c(inp, "C8", "Assumption to review: origination plus gain-on-sale revenue.")
    _c(inp, "A9", "Four-fifths screening threshold")
    _c(inp, "B9", config.FOUR_FIFTHS, BLUE, PCT)
    _c(inp, "C9", "Adverse impact ratio below this value is flagged for review.")
    _c(inp, "A11", "Band limit used by the formulas", bold=True)
    _c(inp, "A12", "Highest DTI band allowed")
    _c(inp, "B12", "=INDEX($F$5:$F$10,MATCH($B$5,$E$5:$E$10,0))", fmt="0")
    _c(inp, "C12", "Band order: 1 <20%, 2 20-29%, 3 30-35%, 4 36-39%, 5 40-44%, 6 45-49%, 7 50-60%, 8 >60%, 9 missing")
    _c(inp, "A13", "Highest LTV band allowed")
    _c(inp, "B13", "=INDEX($I$5:$I$9,MATCH($B$6,$H$5:$H$9,0))", fmt="0")
    _c(inp, "C13", "Band order: 1 <=60%, 2 60-80%, 3 80-90%, 4 90-95%, 5 95-97%, 6 >97%, 7 missing")
    _head(inp, 4, ["DTI cap", "Band"], col=5)
    _head(inp, 4, ["LTV cap", "Band"], col=8)
    for i, (label, order) in enumerate(DTI_CAPS, start=5):
        _c(inp, f"E{i}", label, BLUE)
        _c(inp, f"F{i}", order, BLUE, "0")
    for i, (label, order) in enumerate(LTV_CAPS, start=5):
        _c(inp, f"H{i}", label, BLUE)
        _c(inp, f"I{i}", order, BLUE, "0")
    for ref, options in (("B5", ",".join(x for x, _ in DTI_CAPS)), ("B6", ",".join(x for x, _ in LTV_CAPS)),
                         ("B7", "Yes,No")):
        dv = DataValidation(type="list", formula1=f'"{options}"', allow_blank=False)
        inp.add_data_validation(dv)
        dv.add(ref)
    _widths(inp, {"A": 52, "B": 12, "C": 80, "D": 3, "E": 10, "F": 7, "G": 3, "H": 10, "I": 7})

    # ------------------------------------------------------------------ Grid
    g = wb.create_sheet("Grid")
    _c(g, "A1", "Applications by applicant group, DTI band and LTV band (2025 core sample)", bold=True, size=14)
    _c(g, "A2", SRC, italic=True)
    _head(g, 4, ["Applicant group", "DTI band", "LTV band", "DTI order", "LTV order", "Applications", "Approved",
                 "Denied", "Approved volume ($)", "Passes caps", "Approved after caps", "Approved volume after ($)"])
    first = 5
    grid = grid.sort_values(["applicant_group", "dti_band", "ltv_band"]).reset_index(drop=True)
    for i, r in enumerate(grid.itertuples(), start=first):
        _c(g, f"A{i}", r.applicant_group, BLUE)
        _c(g, f"B{i}", r.dti_band, BLUE)
        _c(g, f"C{i}", r.ltv_band, BLUE)
        _c(g, f"D{i}", f"=VALUE(LEFT(B{i},1))", fmt="0")
        _c(g, f"E{i}", f"=VALUE(LEFT(C{i},1))", fmt="0")
        _c(g, f"F{i}", int(r.applications), BLUE, NUM)
        _c(g, f"G{i}", int(r.approved), BLUE, NUM)
        _c(g, f"H{i}", int(r.denied), BLUE, NUM)
        _c(g, f"I{i}", float(r.approved_volume), BLUE, USD)
        _c(g, f"J{i}", f"=IF(AND(OR(D{i}<=Inputs!$B$12,AND(D{i}=9,Inputs!$B$7=\"Yes\")),"
                       f"OR(E{i}<=Inputs!$B$13,AND(E{i}=7,Inputs!$B$7=\"Yes\"))),1,0)", fmt="0")
        _c(g, f"K{i}", f"=G{i}*J{i}", fmt=NUM)
        _c(g, f"L{i}", f"=I{i}*J{i}", fmt=USD)
    last = first + len(grid) - 1
    g.freeze_panes = "A5"
    _widths(g, {"A": 16, "B": 12, "C": 12, "D": 9, "E": 9, "F": 13, "G": 12, "H": 11, "I": 18, "J": 9, "K": 14,
                "L": 20})
    rng = lambda col: f"Grid!${col}${first}:${col}${last}"  # noqa: E731

    # ------------------------------------------------------------------ Summary
    s = wb.create_sheet("Summary", 1)
    _c(s, "A1", "Policy impact by applicant group", bold=True, size=14)
    _c(s, "A2", '="Caps: DTI "&Inputs!B5&", LTV "&Inputs!B6&". Reference group: White."', italic=True)
    _head(s, 4, ["Applicant group", "Applications", "Approved (2025)", "Approval rate (2025)", "Approved after caps",
                 "Approval rate after caps", "Approval AIR (2025)", "Approval AIR after caps", "Four-fifths screen",
                 "Denial-rate ratio (2025)", "Approvals lost", "Share of group's approvals lost", "Volume lost ($)",
                 "Revenue lost ($)"])
    for i, grp in enumerate(GROUPS, start=5):
        _c(s, f"A{i}", grp, BLUE)
        _c(s, f"B{i}", f"=SUMIFS({rng('F')},{rng('A')},A{i})", fmt=NUM)
        _c(s, f"C{i}", f"=SUMIFS({rng('G')},{rng('A')},A{i})", fmt=NUM)
        _c(s, f"D{i}", f"=IF(B{i}=0,0,C{i}/B{i})", fmt=PCT2)
        _c(s, f"E{i}", f"=SUMIFS({rng('K')},{rng('A')},A{i})", fmt=NUM)
        _c(s, f"F{i}", f"=IF(B{i}=0,0,E{i}/B{i})", fmt=PCT2)
        _c(s, f"G{i}", f"=IF($D$5=0,0,D{i}/$D$5)", fmt=RATIO)
        _c(s, f"H{i}", f"=IF($F$5=0,0,F{i}/$F$5)", fmt=RATIO)
        _c(s, f"I{i}", f"=IF(H{i}<Inputs!$B$9,\"Below threshold\",\"Passes\")")
        _c(s, f"J{i}", f"=IF((1-$D$5)=0,0,(1-D{i})/(1-$D$5))", fmt="0.00")
        _c(s, f"K{i}", f"=C{i}-E{i}", fmt=NUM)
        _c(s, f"L{i}", f"=IF(C{i}=0,0,K{i}/C{i})", fmt=PCT)
        _c(s, f"M{i}", f"=SUMIFS({rng('I')},{rng('A')},A{i})-SUMIFS({rng('L')},{rng('A')},A{i})", fmt=USD)
        _c(s, f"N{i}", f"=M{i}*Inputs!$B$8/10000", fmt=USD)
    t = 5 + len(GROUPS)
    _c(s, f"A{t}", "Total", bold=True)
    for col in "BCEKMN":
        _c(s, f"{col}{t}", f"=SUM({col}5:{col}{t - 1})", fmt=USD if col in "MN" else NUM, bold=True)
    _c(s, f"D{t}", f"=IF(B{t}=0,0,C{t}/B{t})", fmt=PCT2, bold=True)
    _c(s, f"F{t}", f"=IF(B{t}=0,0,E{t}/B{t})", fmt=PCT2, bold=True)
    _c(s, f"L{t}", f"=IF(C{t}=0,0,K{t}/C{t})", fmt=PCT, bold=True)
    s.conditional_formatting.add(f"I5:I{t - 1}", FormulaRule(formula=['I5="Below threshold"'], fill=RED_FILL))
    s.conditional_formatting.add(f"H5:H{t - 1}", CellIsRule(operator="lessThan", formula=["Inputs!$B$9"],
                                                            fill=RED_FILL))
    n = t + 2
    _c(s, f"A{n}", "Reading the table", bold=True)
    notes = [
        "Approval AIR = group approval rate / White approval rate. Values under the threshold on the Inputs sheet "
        "are flagged.",
        "Denial-rate ratio = group denial rate / White denial rate. With approval rates near 90%, small approval "
        "gaps are large denial gaps, so the approval AIR can pass while denial ratios exceed 2.",
        "Volume and revenue lost are first-order: approved loans that the cap would turn away, times the revenue "
        "rate on the Inputs sheet.",
    ]
    for j, text in enumerate(notes, start=n + 1):
        _c(s, f"A{j}", text)
    _widths(s, {"A": 18, **{c: 15 for c in "BCDEFGHIJKLMN"}})
    s.freeze_panes = "B5"

    # ------------------------------------------------------------------ Gap results
    gr = wb.create_sheet("Gap results")
    _c(gr, "A1", "Denial gaps against White applicants (linear probability model)", bold=True, size=14)
    _c(gr, "A2", "Pasted from reports/tables/denial_gap_ladder.csv. Positive = higher denial probability than "
                 "comparable White applicants. Errors clustered by lender.", italic=True)
    _head(gr, 4, ["Specification", "Group", "Gap (pp)", "95% CI low", "95% CI high", "White approval rate (2025)",
                  "Implied approval ratio"])
    for i, r in enumerate(ladder.itertuples(), start=5):
        _c(gr, f"A{i}", r.spec[2:], BLUE)
        _c(gr, f"B{i}", r.group, BLUE)
        _c(gr, f"C{i}", float(r.coef), BLUE, PCT2)
        _c(gr, f"D{i}", float(r.ci_low), BLUE, PCT2)
        _c(gr, f"E{i}", float(r.ci_high), BLUE, PCT2)
        _c(gr, f"F{i}", "=Summary!$D$5", GREEN, PCT2)
        _c(gr, f"G{i}", f"=IF(F{i}=0,0,(F{i}-C{i})/F{i})", fmt=RATIO)
    _widths(gr, {"A": 30, "B": 16, "C": 11, "D": 11, "E": 11, "F": 16, "G": 16})

    # ------------------------------------------------------------------ Lender screen
    ls = wb.create_sheet("Lender screen")
    _c(ls, "A1", "Within-lender denial gaps, largest lenders (screening statistics)", bold=True, size=14)
    _c(ls, "A2", f"Lenders with at least {config.MIN_LENDER_APPS:,} applications in the model sample and "
                 f"{config.MIN_LENDER_GROUP_APPS} Black and Hispanic applicants. Controls plus county fixed effects; "
                 "errors clustered by county. No credit scores in HMDA.", italic=True)
    cols = ["Lender", "Applications", "Denial rate", "Raw gap, Black", "Adjusted gap, Black", "CI low", "CI high",
            "Raw gap, Hispanic", "Adjusted gap, Hispanic", "CI low", "CI high", "Screen"]
    _head(ls, 4, cols)
    for i, r in enumerate(screen.itertuples(), start=5):
        vals = [r.lender_name, r.applications, r.denial_rate, r.raw_gap_black, r.adj_gap_black, r.ci_low_black,
                r.ci_high_black, r.raw_gap_hispanic, r.adj_gap_hispanic, r.ci_low_hispanic, r.ci_high_hispanic,
                r.screen]
        fmts = [None, NUM, PCT, PCT2, PCT2, PCT2, PCT2, PCT2, PCT2, PCT2, PCT2, None]
        for j, (v, f) in enumerate(zip(vals, fmts)):
            cell = ls.cell(row=i, column=1 + j, value=v if not isinstance(v, float) else float(v))
            cell.font = Font(name=ARIAL, color=BLUE)
            if f:
                cell.number_format = f
    _widths(ls, {"A": 36, **{c: 13 for c in "BCDEFGHIJK"}, "L": 34})
    ls.freeze_panes = "B5"

    config.EXCEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    wb.save(config.EXCEL_PATH)
    return str(config.EXCEL_PATH.relative_to(config.ROOT))


def expected_totals(results: dict) -> dict[str, float]:
    """Cell values the recalculated workbook must show with the default (no-cap) inputs."""
    rows = {r["applicant_group"]: r for r in results["groups"]["rates"]}
    out = {}
    for i, grp in enumerate(GROUPS, start=5):
        out[f"Summary!B{i}"] = rows[grp]["applications"]
        out[f"Summary!C{i}"] = rows[grp]["approved"]
        out[f"Summary!E{i}"] = rows[grp]["approved"]
        out[f"Summary!K{i}"] = 0
    return out
