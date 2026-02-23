"""
comprehension_scorer.py — Experiment 2: LLM output production function analysis.

Reads:
  - results/exp2_raw_responses.csv   (LLM response text + token counts)
  - data/code_metrics.csv            (complexity, LoC, nesting per function)

Computes:
  - Output/input token ratio per function
  - Log-log production function: log(output) = alpha + beta * log(input)
  - Output elasticity beta (diminishing marginal returns if beta < 1)
  - CDCC compliance group comparison (Mann-Whitney U)
  - Self-consistency score (SCS) — informational only; equals 1.0 under greedy decoding

Writes: results/exp2_comprehension_scores.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from utils import (
    ANNOTATIONS_DIR, RESULTS_DIR, DATA_DIR, EXP2_RESULTS, get_logger, RANDOM_SEED
)

log = get_logger(__name__)

RAW_RESPONSES_CSV = RESULTS_DIR / "exp2_raw_responses.csv"
CODE_METRICS_CSV  = DATA_DIR / "code_metrics.csv"
EMBEDDING_MODEL   = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Self-Consistency Score (SCS) — kept for completeness
# ---------------------------------------------------------------------------

def compute_scs(responses: list[str], model: SentenceTransformer) -> float:
    """
    Self-consistency score: mean pairwise cosine similarity across all
    N_ATTEMPTS responses for a given function.

    Returns a float in [0, 1]. Note: equals 1.0 when temperature=0 (greedy
    decoding), because the model produces identical strings each attempt.
    """
    if len(responses) < 2:
        return float("nan")
    embeddings = model.encode(responses, show_progress_bar=False)
    sim_matrix = cosine_similarity(embeddings)
    n = len(responses)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    scores = [sim_matrix[i, j] for i, j in pairs]
    return float(np.mean(scores))


# ---------------------------------------------------------------------------
# Production Function Analysis
# ---------------------------------------------------------------------------

def fit_loglog_production_function(
    input_tokens: np.ndarray,
    output_tokens: np.ndarray,
) -> dict:
    """
    Fit log-log model: log(output) = alpha + beta * log(input) + epsilon

    beta < 1 => diminishing marginal returns
    beta = 1 => constant returns
    beta > 1 => increasing returns

    Returns dict with alpha, beta, r_squared, p_value, and interpretation.
    """
    log_input  = np.log(input_tokens)
    log_output = np.log(output_tokens)

    # OLS via scipy linregress
    result = stats.linregress(log_input, log_output)
    beta  = result.slope
    alpha = result.intercept
    r2    = result.rvalue ** 2
    p     = result.pvalue

    if beta < 1:
        interpretation = "diminishing marginal returns (beta < 1)"
    elif beta > 1:
        interpretation = "increasing marginal returns (beta > 1)"
    else:
        interpretation = "constant returns (beta ≈ 1)"

    log.info(
        "Production function: log(output) = %.4f + %.4f * log(input)  "
        "R²=%.4f  p=%.4e  [%s]",
        alpha, beta, r2, p, interpretation,
    )
    return {
        "alpha": round(alpha, 4),
        "beta":  round(beta, 4),
        "r_squared": round(r2, 4),
        "p_value": round(p, 6),
        "interpretation": interpretation,
    }


def compare_cdcc_groups(df: pd.DataFrame) -> dict:
    """
    Mann-Whitney U test comparing output/input ratio between
    CDCC-compliant and CDCC-violating functions.

    Returns summary statistics and test result.
    """
    compliant  = df[~df["cdcc_violation"]]["output_input_ratio"]
    violating  = df[df["cdcc_violation"]]["output_input_ratio"]

    u_stat, p = stats.mannwhitneyu(compliant, violating, alternative="greater")
    ratio_gap = compliant.mean() / violating.mean()

    log.info(
        "CDCC group comparison — compliant: %.4f  violating: %.4f  "
        "ratio gap: %.2f×  U=%.1f  p=%.4e",
        compliant.mean(), violating.mean(), ratio_gap, u_stat, p,
    )
    return {
        "compliant_mean_ratio":  round(compliant.mean(), 4),
        "compliant_n": int(len(compliant)),
        "violating_mean_ratio":  round(violating.mean(), 4),
        "violating_n": int(len(violating)),
        "ratio_gap_x": round(ratio_gap, 2),
        "mann_whitney_u": round(u_stat, 1),
        "p_value": round(p, 6),
    }


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def run() -> pd.DataFrame:
    log.info("Loading raw LLM responses from %s", RAW_RESPONSES_CSV)
    responses_df = pd.read_csv(RAW_RESPONSES_CSV)

    log.info("Loading sentence transformer: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    # --- Per-function aggregation ---
    rows = []
    for func_id, group in responses_df.groupby("function_id"):
        texts = group["response_text"].tolist()
        scs   = compute_scs(texts, model)

        mean_input  = group["input_tokens"].mean()
        mean_output = group["output_tokens"].mean()
        ratio = mean_output / mean_input if mean_input > 0 else float("nan")

        rows.append({
            "function_id":       func_id,
            "scs":               round(scs, 4),
            "mean_input_tokens": round(mean_input, 2),
            "mean_output_tokens": round(mean_output, 2),
            "output_input_ratio": round(ratio, 4),
        })

    results = pd.DataFrame(rows)

    # --- Merge CDCC metrics ---
    if CODE_METRICS_CSV.exists():
        metrics = pd.read_csv(CODE_METRICS_CSV)
        results = results.merge(
            metrics[["function_id", "complexity", "loc",
                     "nesting_depth", "arg_count", "cdcc_violation"]],
            on="function_id",
            how="left",
        )
        log.info("CDCC metrics merged. Violations: %d / %d",
                 results["cdcc_violation"].sum(), len(results))
    else:
        log.warning("code_metrics.csv not found — skipping CDCC group analysis. "
                    "Run: python src/code_metrics.py")
        results["cdcc_violation"] = float("nan")

    # --- Production function ---
    valid = results.dropna(subset=["mean_input_tokens", "mean_output_tokens"])
    pf = fit_loglog_production_function(
        valid["mean_input_tokens"].values,
        valid["mean_output_tokens"].values,
    )
    log.info("Production function: alpha=%.4f  beta=%.4f  R²=%.4f  p=%.4e",
             pf["alpha"], pf["beta"], pf["r_squared"], pf["p_value"])

    # --- CDCC group comparison ---
    if "cdcc_violation" in results.columns and results["cdcc_violation"].notna().any():
        grp = compare_cdcc_groups(results.dropna(subset=["cdcc_violation"]))
        log.info(
            "CDCC group gap: %.3f× (compliant %.4f vs violating %.4f)  p=%.4e",
            grp["ratio_gap_x"],
            grp["compliant_mean_ratio"],
            grp["violating_mean_ratio"],
            grp["p_value"],
        )

    results.to_csv(EXP2_RESULTS, index=False)
    log.info("Comprehension scores written to %s", EXP2_RESULTS)
    return results


if __name__ == "__main__":
    run()
