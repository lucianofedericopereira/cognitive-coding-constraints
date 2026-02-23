"""
cost_model.py — Experiment 1: actuarial cost projection.

Reproduces and extends the enterprise cost model from Pereira (2026a)
using empirically measured inter-notation token ratios instead of
the theoretical 1.67x estimate.

Outputs a printed report and updates results/exp1_token_counts.csv
with a 'cost_delta_usd' column (per row, for sensitivity analysis).

Confidence intervals are computed via non-parametric bootstrap
(N_BOOTSTRAP = 10_000) on the distribution of per-identifier ratios.
"""

import numpy as np
import pandas as pd
from utils import EXP1_RESULTS, RANDOM_SEED, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# Default parameters (override via CLI args or direct import)
# ---------------------------------------------------------------------------
DAILY_API_CALLS: int = 1_000_000
TOKENS_PER_CALL: int = 150        # mean event-identifier context window share
COST_PER_1K_TOKENS: float = 0.005  # USD, GPT-4o input pricing at time of writing
N_BOOTSTRAP: int = 10_000
CI_LEVEL: float = 0.95

rng = np.random.default_rng(RANDOM_SEED)


# ---------------------------------------------------------------------------
# Cost formula
# ---------------------------------------------------------------------------

def annual_cost_delta(
    mean_ratio: float,
    daily_calls: int = DAILY_API_CALLS,
    tokens_per_call: int = TOKENS_PER_CALL,
    cost_per_1k: float = COST_PER_1K_TOKENS,
) -> float:
    """
    Compute annualised USD cost difference between dot notation and camelCase.

    Formula from Pereira (2026a):
      delta = (ratio - 1.0) * daily_calls * tokens_per_call * (cost_per_1k / 1000) * 365
    """
    return (mean_ratio - 1.0) * daily_calls * tokens_per_call * (cost_per_1k / 1_000) * 365


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------

def bootstrap_ci(
    ratios: np.ndarray,
    n_bootstrap: int = N_BOOTSTRAP,
    ci_level: float = CI_LEVEL,
    daily_calls: int = DAILY_API_CALLS,
    tokens_per_call: int = TOKENS_PER_CALL,
    cost_per_1k: float = COST_PER_1K_TOKENS,
) -> dict:
    """Return point estimate and bootstrapped CI for annual_cost_delta."""
    bootstrap_deltas = []
    for _ in range(n_bootstrap):
        sample = rng.choice(ratios, size=len(ratios), replace=True)
        bootstrap_deltas.append(
            annual_cost_delta(sample.mean(), daily_calls, tokens_per_call, cost_per_1k)
        )
    bootstrap_deltas = np.array(bootstrap_deltas)
    alpha = (1 - ci_level) / 2
    lo = np.quantile(bootstrap_deltas, alpha)
    hi = np.quantile(bootstrap_deltas, 1 - alpha)
    point = annual_cost_delta(ratios.mean(), daily_calls, tokens_per_call, cost_per_1k)
    return {
        "point_estimate_usd": round(point, 2),
        f"ci_{int(ci_level*100)}_lo_usd": round(lo, 2),
        f"ci_{int(ci_level*100)}_hi_usd": round(hi, 2),
        "mean_ratio": round(float(ratios.mean()), 4),
        "std_ratio": round(float(ratios.std()), 4),
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run(
    tokenizer: str = "gpt4o",
    daily_calls: int = DAILY_API_CALLS,
    tokens_per_call: int = TOKENS_PER_CALL,
    cost_per_1k: float = COST_PER_1K_TOKENS,
) -> dict:
    log.info("Loading experiment 1 results from %s", EXP1_RESULTS)
    df = pd.read_csv(EXP1_RESULTS)

    sub = df[df["tokenizer"] == tokenizer].copy()
    if sub.empty:
        raise ValueError(f"Tokenizer '{tokenizer}' not found in {EXP1_RESULTS}")

    ratio_col = "dot_vs_camelCase_ratio"
    if ratio_col not in sub.columns:
        sub[ratio_col] = sub["dot_tokens"] / sub["camelCase_tokens"]

    ratios = sub[ratio_col].dropna().values
    result = bootstrap_ci(ratios, N_BOOTSTRAP, CI_LEVEL, daily_calls, tokens_per_call, cost_per_1k)
    result["tokenizer"] = tokenizer
    result["daily_api_calls"] = daily_calls
    result["tokens_per_call"] = tokens_per_call
    result["cost_per_1k_usd"] = cost_per_1k

    ci = int(CI_LEVEL * 100)
    log.info(
        "\n=== Cost Projection (tokenizer=%s) ===\n"
        "  Mean dot/camelCase ratio : %.4f (+/-%.4f)\n"
        "  Annual cost delta        : $%s\n"
        "  %d%% CI                   : [$%s, $%s]",
        tokenizer,
        result["mean_ratio"], result["std_ratio"],
        f"{result['point_estimate_usd']:,.2f}",
        ci,
        f"{result[f'ci_{ci}_lo_usd']:,.2f}",
        f"{result[f'ci_{ci}_hi_usd']:,.2f}",
    )
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Actuarial cost projection (Pereira 2026a)")
    parser.add_argument("--tokenizer", default="gpt4o")
    parser.add_argument("--daily-calls", type=int, default=DAILY_API_CALLS)
    parser.add_argument("--tokens-per-call", type=int, default=TOKENS_PER_CALL)
    parser.add_argument("--cost-per-1k", type=float, default=COST_PER_1K_TOKENS)
    args = parser.parse_args()

    run(
        tokenizer=args.tokenizer,
        daily_calls=args.daily_calls,
        tokens_per_call=args.tokens_per_call,
        cost_per_1k=args.cost_per_1k,
    )
