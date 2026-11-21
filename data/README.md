# Data

`make data` downloads three public files into `raw/` (no account needed) and writes `raw/MANIFEST.json` with
each file's size, SHA-256 checksum and URL. `make pipeline` builds `processed/hmda.duckdb`. Both folders are
git-ignored; the files are not redistributed here.

| File | Source | Size | Grain |
|---|---|---|---|
| hmda_2025_home_purchase.csv | HMDA Data Browser API (CFPB / FFIEC), nationwide, 2025, loan purpose 1 (home purchase), action taken 1, 2, 3 | about 1.7 GB, 4.36 million rows, 99 columns | one loan application with a credit decision |
| filers_2025.json | HMDA filers list, https://ffiec.cfpb.gov/v2/reporting/filers/2025 | 0.4 MB | lender LEI and name |
| national_county2020.txt | U.S. Census Bureau 2020 county codes | 0.1 MB | county FIPS code and name |

Download URL for the application records:
`https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv?years=2025&loan_purposes=1&actions_taken=1,2,3`
(the API redirects to a cached snapshot file on files.ffiec.cfpb.gov).

The public HMDA file is the modified loan application register: the CFPB removes or bands fields that could
identify a borrower (no application date, no credit score, loan amounts at the midpoint of $10,000 bins, age
and DTI in bands). Field definitions: the CFPB's public HMDA data fields documentation,
https://ffiec.cfpb.gov/documentation/publications/loan-level-datasets/lar-data-fields.
