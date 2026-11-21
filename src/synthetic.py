"""Synthetic HMDA-shaped records for the test suite (never used for results).

The generator plants known effects: denial probability rises with DTI above 49% and is `black_effect`
higher for Black applicants, so tests can check that the SQL and the regressions recover them.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

LEIS = [f"TESTLEI{i:013d}" for i in range(12)]


def write(raw_dir: Path, n: int = 6000, seed: int = 0, black_effect: float = 0.10) -> None:
    rng = np.random.default_rng(seed)
    raw_dir.mkdir(parents=True, exist_ok=True)
    group = rng.choice(["White", "Black", "Hispanic", "Asian"], size=n, p=[0.55, 0.2, 0.15, 0.1])
    eth = np.where(group == "Hispanic", "Hispanic or Latino", "Not Hispanic or Latino")
    race = np.select([group == "Black", group == "Asian"], ["Black or African American", "Asian"], "White")
    dti_codes = np.array(["<20%", "20%-<30%", "30%-<36%"] + [str(x) for x in range(36, 50)] + ["50%-60%", ">60%"])
    dti = rng.choice(dti_codes, size=n)
    high_dti = np.isin(dti, ["50%-60%", ">60%"])
    p_deny = 0.05 + 0.5 * high_dti + black_effect * (group == "Black")
    denied = rng.random(n) < p_deny
    action = np.where(denied, "3", np.where(rng.random(n) < 0.97, "1", "2"))
    counties = np.array(["48201", "48113", "06037", "17031", "13121"])
    county = rng.choice(counties, size=n)
    fips_state = {"48": "TX", "06": "CA", "17": "IL", "13": "GA"}
    state = np.array([fips_state[c[:2]] for c in county])
    income = rng.lognormal(np.log(110), 0.4, n).round()
    loan = (rng.lognormal(np.log(320000), 0.4, n) / 10000).round() * 10000 + 5000
    ltv = rng.uniform(50, 100, n).round(2)
    frame = pd.DataFrame({
        "activity_year": "2025", "lei": rng.choice(LEIS, size=n), "derived_msa-md": "26420", "state_code": state,
        "county_code": county, "census_tract": [c + f"{i % 900 + 100:06d}" for i, c in enumerate(county)],
        "conforming_loan_limit": "C", "derived_dwelling_category": "Single Family (1-4 Units):Site-Built",
        "derived_ethnicity": eth, "derived_race": race, "derived_sex": rng.choice(["Male", "Female", "Joint"], size=n),
        "action_taken": action, "preapproval": "2", "loan_type": rng.choice(["1", "2", "3"], size=n, p=[0.7, 0.2, 0.1]),
        "loan_purpose": "1", "lien_status": "1", "reverse_mortgage": "2", "open-end_line_of_credit": "2",
        "business_or_commercial_purpose": "2", "loan_amount": loan.astype(int).astype(str),
        "loan_to_value_ratio": ltv.astype(str), "interest_rate": np.where(action == "1", "6.5", "NA"),
        "rate_spread": np.where(action == "1", rng.normal(0.2, 0.3, n).round(3).astype(str), "NA"),
        "total_loan_costs": "6000", "discount_points": "NA", "loan_term": "360", "intro_rate_period": "NA",
        "negative_amortization": "2", "interest_only_payment": "2", "balloon_payment": "2",
        "other_nonamortizing_features": "2", "property_value": (loan / ltv * 100).round(-4).astype(int).astype(str),
        "occupancy_type": "1", "income": income.astype(int).astype(str), "debt_to_income_ratio": dti,
        "applicant_credit_score_type": "1", "applicant_age": rng.choice(["25-34", "35-44", "45-54"], size=n),
        "submission_of_application": "1", "aus-1": "1",
        "denial_reason-1": np.where(denied, np.where(high_dti, "1", "3"), "10"), "denial_reason-2": "",
        "denial_reason-3": "", "denial_reason-4": "", "tract_minority_population_percent": rng.uniform(0, 100, n).round(2),
        "ffiec_msa_md_median_family_income": "100000", "tract_to_msa_income_percentage": rng.uniform(40, 200, n).round(),
    })
    frame.to_csv(raw_dir / "hmda_2025_home_purchase.csv", index=False)
    (raw_dir / "filers_2025.json").write_text(json.dumps(
        {"institutions": [{"lei": lei, "name": f"Test Lender {i}", "period": "2025"} for i, lei in enumerate(LEIS)]}))
    rows = ["STATE|STATEFP|COUNTYFP|COUNTYNS|COUNTYNAME|CLASSFP|FUNCSTAT"]
    names = {"48201": ("TX", "Harris County"), "48113": ("TX", "Dallas County"), "06037": ("CA", "Los Angeles County"),
             "17031": ("IL", "Cook County"), "13121": ("GA", "Fulton County")}
    rows += [f"{st}|{c[:2]}|{c[2:]}|0|{nm}|H1|A" for c, (st, nm) in names.items()]
    (raw_dir / "national_county2020.txt").write_text("\n".join(rows) + "\n")
