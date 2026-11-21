# Power BI report

`MortgageFairLending.pbip` is a Power BI project (PBIP) written by `src/powerbi.py`:

* `MortgageFairLending.SemanticModel/`: TMDL model with 9 tables loaded from `data/*.csv`: the application fact
  table (state x loan type x applicant group x DTI band x LTV band, sums only), income and tract table, DTI
  profile, denial reasons, gap ladder, pricing gaps, lender screen, county rates and an applicant group
  dimension. Five relationships to the group dimension; DAX measures in display folders (Volume, Rates, Fair
  lending, Underwriting), including approval-rate adverse impact ratio and denial-rate ratio against White
  applicants computed with `CALCULATE`.
* `MortgageFairLending.Report/`: PBIR report with four pages. *Market overview*: volume and rate cards, denial
  rate by loan type and state, applications by group, county table. *Underwriting drivers*: denial rate by
  exact DTI, by LTV band, DTI x LTV matrix, denial reasons by group. *Fair-lending screen*: approval and denial
  ratios by group with the four-fifths flag, gap ladder, tract x income matrix, pricing gaps. *Lender screen*:
  within-lender adjusted gaps for the largest lenders.

## Open it (Windows, Power BI Desktop)
1. Open `MortgageFairLending.pbip`.
2. Transform data > Edit parameters > set **DataFolder** to the full path of this folder's `data\` subfolder,
   ending with a backslash, for example
   `C:\Users\you\hmda-mortgage-approval-fair-lending\dashboards\powerbi\data\`.
3. Close & Apply (or Refresh).

## Checks done here
The report's JSON files validate against Microsoft's PBIR schemas (`visualContainer/2.4.0`, `page/2.0.0`,
`report/3.0.0`). Power BI Desktop is not available on macOS, so the report has not been opened in Desktop;
`report_preview.png` is a Python rendering of the Fair-lending screen page from the same CSVs.
