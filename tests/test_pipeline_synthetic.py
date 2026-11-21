"""End-to-end check on synthetic HMDA-shaped data with a planted effect (see src/synthetic.py)."""
import pytest

from src import config, data, fairlending, synthetic
from src.stats import oaxaca


@pytest.fixture(scope="module")
def warehouse(tmp_path_factory):
    raw = tmp_path_factory.mktemp("raw")
    synthetic.write(raw, n=6000, black_effect=0.10)
    mp = pytest.MonkeyPatch()
    for name, value in {"RAW_DIR": raw, "DB_PATH": raw / "test.duckdb", "LAR_CSV": raw / "hmda_2025_home_purchase.csv",
                        "FILERS_JSON": raw / "filers_2025.json", "COUNTY_TXT": raw / "national_county2020.txt",
                        "MIN_ROWS": 1000, "MIN_COUNTY_APPS": 10}.items():
        mp.setattr(config, name, value)
    checks = data.build_warehouse()
    yield checks
    mp.undo()


def test_hard_rules_pass_and_counts_add_up(warehouse):
    assert (warehouse[warehouse.severity == "hard"].failures == 0).all()
    counts = data.row_counts()
    assert counts["lar_raw"] == counts["applications"] == 6000
    rates = data.query("05_group_rates.sql")
    allrows = rates[rates.loan_type == "All"]
    assert allrows.applications.sum() == counts["core"]
    assert (allrows.approved + allrows.denied == allrows.applications).all()


def test_dti_bands_and_cliff(warehouse):
    dti = data.query("06_dti_profile.sql")
    conv = dti[dti.loan_type == "Conventional"].set_index("dti_value")
    assert conv.loc[55, "denial_rate"] > conv.loc[40, "denial_rate"] + 0.3
    assert set(dti.dti_band) <= {"1 <20%", "2 20-29%", "3 30-35%", "4 36-39%", "5 40-44%", "6 45-49%", "7 50-60%",
                                 "8 >60%"}


def test_gap_ladder_recovers_planted_effect(warehouse):
    df = data.model_frame()
    ladder, _ = fairlending.gap_ladder(df)
    b2 = ladder[(ladder.spec.str.startswith("2")) & (ladder.group == "Black")].iloc[0]
    assert b2.ci_low < 0.10 < b2.ci_high
    h2 = ladder[(ladder.spec.str.startswith("2")) & (ladder.group == "Hispanic")].iloc[0]
    assert h2.ci_low < 0 < h2.ci_high


def test_oaxaca_parts_add_up(warehouse):
    df = data.model_frame()
    o = oaxaca(df, "Black")
    assert o["explained"] + o["unexplained"] == pytest.approx(o["raw_gap"], abs=1e-9)


def test_policy_grid_matches_group_rates(warehouse):
    grid = data.query("13_policy_grid.sql")
    rates = data.query("05_group_rates.sql")
    allrows = rates[rates.loan_type == "All"].set_index("applicant_group")
    by_group = grid.groupby("applicant_group").approved.sum()
    for g, v in by_group.items():
        assert v == allrows.loc[g, "approved"]
