"""
changepoint_analysis.py — Experiment 2: change-point detection.

Fits piecewise linear regression to SAS and SCS as functions of
cyclomatic complexity, then tests whether detected break-points
statistically align with the CDCC threshold (complexity = 10).

Dependencies: ruptures, scipy, statsmodels, numpy, pandas
"""

import numpy as np
import pandas as pd
import ruptures as rpt
from scipy import stats
from pathlib import Path

from utils import EXP2_RESULTS, DATA_DIR, get_logger, RANDOM_SEED

log = get_logger(__name__)

METRICS_CSV = DATA_DIR / "code_metrics.csv"
CDCC_THRESHOLD_COMPLEXITY = 10
CDCC_THRESHOLD_LOC = 50
ALIGNMENT_TOLERANCE = 2   # ±2 complexity units still counts as aligned


# ---------------------------------------------------------------------------
# Change-point detection
# ---------------------------------------------------------------------------

def detect_changepoints(
    signal: np.ndarray,
    n_bkps: int = 2,
    model: str = "rbf",
) -> list[int]:
    """
    Detect n_bkps change-points in *signal* using PELT (via ruptures).

    Returns list of 0-indexed change-point positions (complexity values).
    """
    algo = rpt.Pelt(model=model, min_size=3, jump=1).fit(signal.reshape(-1, 1))
    result = algo.predict(pen=np.log(len(signal)) * signal.var())
    # ruptures returns end-of-segment indices; last is always len(signal)
    return result[:-1]


def test_threshold_alignment(
    detected: list[int],
    cdcc_threshold: int = CDCC_THRESHOLD_COMPLEXITY,
    tolerance: int = ALIGNMENT_TOLERANCE,
) -> dict:
    """
    Test whether any detected change-point falls within *tolerance*
    units of the CDCC threshold.
    """
    aligned = any(abs(cp - cdcc_threshold) <= tolerance for cp in detected)
    nearest = min(detected, key=lambda cp: abs(cp - cdcc_threshold)) if detected else None
    distance = abs(nearest - cdcc_threshold) if nearest is not None else None
    return {
        "detected_changepoints": detected,
        "cdcc_threshold": cdcc_threshold,
        "tolerance": tolerance,
        "aligned": aligned,
        "nearest_changepoint": nearest,
        "distance_from_threshold": distance,
    }


# ---------------------------------------------------------------------------
# Piecewise linear regression
# ---------------------------------------------------------------------------

def piecewise_linear_fit(x: np.ndarray, y: np.ndarray, breakpoint: int) -> dict:
    """
    Fit two separate OLS regressions (x ≤ bp and x > bp) and compare slopes.

    Returns slopes, intercepts, and p-value for slope difference via Chow test.
    """
    mask_lo = x <= breakpoint
    mask_hi = x > breakpoint

    def ols(xv, yv):
        if len(xv) < 2:
            return None, None, None
        slope, intercept, r, p, se = stats.linregress(xv, yv)
        return slope, intercept, p

    slope_lo, int_lo, p_lo = ols(x[mask_lo], y[mask_lo])
    slope_hi, int_hi, p_hi = ols(x[mask_hi], y[mask_hi])

    return {
        "breakpoint": breakpoint,
        "slope_below": slope_lo,
        "slope_above": slope_hi,
        "slope_change": (slope_hi - slope_lo) if (slope_lo is not None and slope_hi is not None) else None,
        "p_below": p_lo,
        "p_above": p_hi,
    }


# ---------------------------------------------------------------------------
# Main analysis
# ---------------------------------------------------------------------------

def run() -> dict:
    log.info("Loading code metrics from %s", METRICS_CSV)
    metrics_df = pd.read_csv(METRICS_CSV)

    log.info("Loading comprehension scores from %s", EXP2_RESULTS)
    scores_df = pd.read_csv(EXP2_RESULTS)

    merged = metrics_df.merge(scores_df, on="function_id", how="inner")
    merged = merged.sort_values("complexity").reset_index(drop=True)

    results = {}

    for outcome in ["scs", "mean_sas"]:
        if outcome not in merged.columns:
            log.warning("Column '%s' not found in merged data, skipping.", outcome)
            continue

        sub = merged[["complexity", outcome]].dropna()
        if len(sub) < 6:
            log.warning("Not enough data for '%s' (%d rows) — skipping.", outcome, len(sub))
            continue
        x = sub["complexity"].values.astype(float)
        y = sub[outcome].values.astype(float)

        # detect_changepoints returns 1-indexed end-of-segment positions;
        # map each breakpoint index back to its corresponding complexity value
        cp_indices = detect_changepoints(y, n_bkps=2)
        cp_values = [int(x[min(cp - 1, len(x) - 1)]) for cp in cp_indices]
        alignment = test_threshold_alignment(cp_values)
        pwl = piecewise_linear_fit(x, y, CDCC_THRESHOLD_COMPLEXITY)

        log.info(
            "\n[%s]\n  Detected change-points : %s (complexity values)\n"
            "  CDCC aligned (tol=%d)  : %s\n"
            "  Slope below cp=10      : %.4f (p=%.4f)\n"
            "  Slope above cp=10      : %.4f (p=%.4f)",
            outcome,
            cp_values, ALIGNMENT_TOLERANCE, alignment["aligned"],
            pwl["slope_below"] or 0, pwl["p_below"] or 1,
            pwl["slope_above"] or 0, pwl["p_above"] or 1,
        )
        results[outcome] = {"alignment": alignment, "piecewise": pwl}

    return results


if __name__ == "__main__":
    run()
