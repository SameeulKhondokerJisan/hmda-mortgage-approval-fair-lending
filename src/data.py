"""Build the DuckDB warehouse from the raw HMDA file and expose query helpers."""
from __future__ import annotations

import re

import duckdb
import pandas as pd

from src import config


class DataQualityError(RuntimeError):
    """Raised when a hard data-quality rule fails."""


def split_statements(sql: str) -> list[str]:
    no_comments = re.sub(r"--[^\n]*", "", sql)
    return [s.strip() for s in no_comments.split(";") if s.strip()]


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    config.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(config.DB_PATH), read_only=read_only)


def fill(sql: str, **params) -> str:
    base = {"lar_csv": config.LAR_CSV.as_posix(), "filers_json": config.FILERS_JSON.as_posix(),
            "county_txt": config.COUNTY_TXT.as_posix(), "min_rows": config.MIN_ROWS,
            "min_rows_fmt": f"{config.MIN_ROWS:,}", "min_county_apps": config.MIN_COUNTY_APPS}
    for key, value in {**base, **params}.items():
        sql = sql.replace("{" + key + "}", str(value))
    return sql


def run_sql(con, filename: str, **params) -> pd.DataFrame | None:
    """Run every statement of a SQL file and return the result of the last one."""
    result = None
    for statement in split_statements(fill((config.SQL_DIR / filename).read_text(), **params)):
        result = con.execute(statement)
    try:
        return result.df() if result is not None else None
    except duckdb.Error:
        return None


def build_warehouse() -> pd.DataFrame:
    """Load, type and check the data. Returns the quality-check report."""
    for path in (config.LAR_CSV, config.FILERS_JSON, config.COUNTY_TXT):
        if not path.exists():
            raise FileNotFoundError(f"{path} is missing. Run `python -m src.download_data` first.")
    with connect() as con:
        run_sql(con, "01_load.sql")
        run_sql(con, "02_applications.sql")
        checks = run_sql(con, "03_quality_checks.sql")
    failed = checks[(checks.severity == "hard") & (checks.failures > 0)]
    if not failed.empty:
        raise DataQualityError("Hard data-quality rules failed:\n" + failed.to_string(index=False))
    return checks


def query(filename_or_sql: str, **params) -> pd.DataFrame:
    with connect(read_only=True) as con:
        if filename_or_sql.endswith(".sql"):
            return run_sql(con, filename_or_sql, **params)
        return con.execute(fill(filename_or_sql, **params)).df()


def row_counts() -> dict[str, int]:
    with connect(read_only=True) as con:
        return {n: int(con.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0])
                for n in ("lar_raw", "applications", "core", "model_frame", "lenders", "counties")}


MODEL_COLUMNS = ["app_id", "lei", "state_code", "county_fips", "loan_type", "applicant_group", "sex", "age_band",
                 "income_k", "loan_amount", "property_value", "ltv", "dti_band", "ltv_band", "conforming",
                 "preapproval", "direct_application", "tract_income_band", "tract_minority_band", "denied",
                 "originated", "rate_spread", "interest_rate", "discount_points", "loan_term", "fixed_amortizing"]


def model_frame() -> pd.DataFrame:
    """Applications with every underwriting control (see sql/02_applications.sql, view model_frame)."""
    df = query("SELECT " + ", ".join(MODEL_COLUMNS) + " FROM model_frame")
    for col in ("lei", "state_code", "county_fips", "loan_type", "applicant_group", "sex", "age_band", "dti_band",
                "ltv_band", "tract_income_band", "tract_minority_band"):
        df[col] = df[col].astype("category")
    return df
