"""Paths, sample definition and analysis settings."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# HMDA_RAW_DIR / HMDA_DB_PATH / HMDA_MIN_ROWS let the test suite run the pipeline on a small sample.
RAW_DIR = Path(os.environ.get("HMDA_RAW_DIR", ROOT / "data" / "raw"))
DB_PATH = Path(os.environ.get("HMDA_DB_PATH", ROOT / "data" / "processed" / "hmda.duckdb"))
MIN_ROWS = int(os.environ.get("HMDA_MIN_ROWS", 4_000_000))
LAR_CSV = RAW_DIR / "hmda_2025_home_purchase.csv"
FILERS_JSON = RAW_DIR / "filers_2025.json"
COUNTY_TXT = RAW_DIR / "national_county2020.txt"
SQL_DIR = ROOT / "sql"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
TABLES = REPORTS / "tables"
RESULTS_JSON = REPORTS / "results.json"
POWERBI_DIR = ROOT / "dashboards" / "powerbi"
POWERBI_DATA = POWERBI_DIR / "data"
EXCEL_PATH = ROOT / "excel" / "underwriting_policy_fair_lending_model.xlsx"

YEAR = 2025
# HMDA Data Browser API (CFPB / FFIEC): every 2025 home-purchase application that reached a decision.
LAR_URL = ("https://ffiec.cfpb.gov/v2/data-browser-api/view/nationwide/csv"
           "?years=2025&loan_purposes=1&actions_taken=1,2,3")
FILERS_URL = "https://ffiec.cfpb.gov/v2/reporting/filers/2025"
COUNTY_URL = "https://www2.census.gov/geo/docs/reference/codes2020/national_county2020.txt"

REFERENCE_GROUP = "White"
# Applicant groups compared with the reference group in every gap estimate.
GROUPS = ["Black", "Hispanic", "Asian", "Other minority"]
GROUP_ORDER = ["White", "Black", "Hispanic", "Asian", "Other minority", "Joint", "Not reported"]

MIN_LENDER_APPS = 5000        # lenders screened individually need this many core applications ...
MIN_LENDER_GROUP_APPS = 300   # ... and this many Black and this many Hispanic applicants
MIN_COUNTY_APPS = 500         # counties shown on the map need this many core applications
LOGIT_SAMPLE = 600_000        # rows used for the logistic-regression robustness check
SEED = 42
FOUR_FIFTHS = 0.80            # adverse impact ratio screening threshold

# Excel underwriting simulator defaults (current practice: no extra cap)
DEFAULT_DTI_CAP = "No cap"
DEFAULT_LTV_CAP = "No cap"
GAIN_ON_SALE_BPS = 100        # revenue per originated dollar, basis points (assumption, editable in Excel)
