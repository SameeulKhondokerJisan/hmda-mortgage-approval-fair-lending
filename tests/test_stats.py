"""Statistics helpers: Wilson interval, fixed-effects OLS, Oaxaca-Blinder identity, policy simulator."""
import numpy as np
import pandas as pd
import pytest

from src import fairlending
from src.stats import ols, wilson


def test_wilson_matches_reference_values():
    lo, hi = wilson(np.array([10]), np.array([100]))
    assert lo[0] == pytest.approx(0.0552, abs=1e-4)
    assert hi[0] == pytest.approx(0.1744, abs=1e-4)


def test_absorbed_fixed_effect_recovers_slope_and_ignores_group_shift():
    rng = np.random.default_rng(1)
    n, groups = 20000, 400
    g = rng.integers(0, groups, n)
    alpha = rng.normal(0, 5, groups)
    x = rng.normal(0, 1, n) + 0.5 * alpha[g]          # x correlated with the fixed effect
    y = 2.0 * x + alpha[g] + rng.normal(0, 1, n)
    naive = ols(y, pd.DataFrame({"x": x})).coef.set_index("term").loc["x", "coef"]
    fe = ols(y, pd.DataFrame({"x": x}), absorb=g, cluster=g).coef.set_index("term").loc["x"]
    assert abs(naive - 2.0) > 0.2                       # omitted fixed effect biases the naive slope
    assert fe.coef == pytest.approx(2.0, abs=0.03)
    assert fe.ci_low < 2.0 < fe.ci_high


def test_simulator_without_caps_changes_nothing_and_caps_only_remove():
    grid = pd.DataFrame({"applicant_group": ["White", "White", "Black", "Black"],
                         "dti_band": ["3 30-35%", "7 50-60%", "3 30-35%", "7 50-60%"],
                         "ltv_band": ["2 60-80%", "2 60-80%", "6 >97%", "2 60-80%"],
                         "applications": [100, 20, 50, 30], "approved": [95, 6, 45, 9], "denied": [5, 14, 5, 21],
                         "approved_volume": [9.5e6, 6e5, 4.5e6, 9e5]})
    base = fairlending.simulate_policy(grid).set_index("applicant_group")
    assert (base.approvals_lost == 0).all()
    capped = fairlending.simulate_policy(grid, dti_max=6, ltv_max=5).set_index("applicant_group")
    assert capped.loc["White", "approvals_lost"] == 6
    assert capped.loc["Black", "approvals_lost"] == 54
    assert capped.loc["Black", "air_after"] == pytest.approx(0 / 80 / (95 / 120))
