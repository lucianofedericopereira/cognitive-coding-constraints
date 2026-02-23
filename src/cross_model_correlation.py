# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
cross_model_correlation.py — Experiment 3: cross-model tokenizer variance (RQ4).

Computes Spearman rank correlations of naming-convention efficiency rankings
across all tokenizers tested in Experiment 1.

If ρ > 0.85 for all pairs, the camelCase efficiency advantage is robust
across vocabulary differences (Hypothesis H2 from the paper).

Writes: results/exp3_rank_correlations.csv
"""

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from itertools import combinations

from utils import EXP1_RESULTS, EXP3_RESULTS, get_logger

log = get_logger(__name__)

NOTATION_COLS = ["dot", "camelCase", "snake_case", "kebab_case"]
ROBUSTNESS_THRESHOLD = 0.85


# ---------------------------------------------------------------------------
# Ranking helpers
# ---------------------------------------------------------------------------

def rank_by_efficiency(df: pd.DataFrame, tokenizer: str) -> pd.Series:
    """
    For a given tokenizer, compute mean token count per notation across the
    corpus and return a rank Series (1 = most efficient = fewest tokens).

    Index: notation names. Values: ranks (1–4).
    """
    sub = df[df["tokenizer"] == tokenizer]
    means = {n: sub[f"{n}_tokens"].mean() for n in NOTATION_COLS}
    ranked = pd.Series(means).rank(ascending=True)   # lower tokens = better rank
    return ranked


# ---------------------------------------------------------------------------
# Correlation matrix
# ---------------------------------------------------------------------------

def cross_model_correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute pairwise Spearman rank correlation of notation efficiency rankings
    across all tokenizer pairs.

    Returns a DataFrame with columns: tok_a, tok_b, spearman_rho, p_value.
    """
    tokenizers = df["tokenizer"].unique().tolist()
    rankings = {tok: rank_by_efficiency(df, tok) for tok in tokenizers}

    rows = []
    for tok_a, tok_b in combinations(tokenizers, 2):
        rank_a = rankings[tok_a][NOTATION_COLS].values
        rank_b = rankings[tok_b][NOTATION_COLS].values
        rho, p = spearmanr(rank_a, rank_b)
        rows.append({
            "tokenizer_a": tok_a,
            "tokenizer_b": tok_b,
            "spearman_rho": round(rho, 4),
            "p_value": round(p, 6),
            "robust": rho >= ROBUSTNESS_THRESHOLD,
        })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> pd.DataFrame:
    log.info("Loading experiment 1 results from %s", EXP1_RESULTS)
    df = pd.read_csv(EXP1_RESULTS)

    corr_matrix = cross_model_correlation_matrix(df)
    corr_matrix.to_csv(EXP3_RESULTS, index=False)
    log.info("Rank correlation matrix written to %s", EXP3_RESULTS)

    all_robust = corr_matrix["robust"].all()
    min_rho = corr_matrix["spearman_rho"].min()

    log.info(
        "\n=== Cross-model Spearman rank correlations ===\n%s\n\n"
        "H2 (ρ > %.2f for all pairs): %s  (min ρ = %.4f)",
        corr_matrix.to_string(index=False),
        ROBUSTNESS_THRESHOLD,
        "SUPPORTED" if all_robust else "NOT SUPPORTED",
        min_rho,
    )

    return corr_matrix


if __name__ == "__main__":
    run()