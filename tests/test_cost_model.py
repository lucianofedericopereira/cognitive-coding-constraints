"""Unit tests for cost_model.py actuarial formula."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from cost_model import annual_cost_delta, bootstrap_ci
import numpy as np


def test_annual_cost_delta_no_overhead():
    assert annual_cost_delta(1.0) == 0.0


def test_annual_cost_delta_theoretical_ratio():
    # Pereira 2026a: 1.67x ratio, 1M calls/day, 150 tokens, $0.005/1k
    result = annual_cost_delta(1.67, daily_calls=1_000_000, tokens_per_call=150, cost_per_1k=0.005)
    # 0.67 * 1e6 * 150 * 5e-6 * 365 = 183,412.5
    assert abs(result - 183_412.5) < 1.0


def test_bootstrap_ci_shape():
    rng = np.random.default_rng(42)
    ratios = rng.normal(loc=1.4, scale=0.1, size=200)
    result = bootstrap_ci(ratios, n_bootstrap=500)
    assert "point_estimate_usd" in result
    assert result["ci_95_lo_usd"] <= result["point_estimate_usd"] <= result["ci_95_hi_usd"]
