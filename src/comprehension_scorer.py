"""
comprehension_scorer.py — Experiment 2: SAS and SCS computation.

Reads:
  - data/annotations/rater_a.csv, rater_b.csv  (manual SAS scores)
  - results/exp2_raw_responses.csv              (LLM response text)

Computes:
  - SAS: manual annotation reconciliation + Cohen's κ
  - SCS: mean pairwise cosine similarity of response embeddings per function
  - Output/Input ratio analysis

Writes: results/exp2_comprehension_scores.csv
"""

import numpy as np
import pandas as pd
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics import cohen_kappa_score
from sklearn.metrics.pairwise import cosine_similarity

from utils import (
    ANNOTATIONS_DIR, RESULTS_DIR, EXP2_RESULTS, get_logger, RANDOM_SEED
)

log = get_logger(__name__)

RAW_RESPONSES_CSV = RESULTS_DIR / "exp2_raw_responses.csv"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


# ---------------------------------------------------------------------------
# Self-Consistency Score (SCS)
# ---------------------------------------------------------------------------

def compute_scs(responses: list[str], model: SentenceTransformer) -> float:
    """
    Self-consistency score: mean pairwise cosine similarity across all
    N_ATTEMPTS responses for a given function.

    Returns a float in [0, 1]. Higher = more consistent = less instability.
    """
    if len(responses) < 2:
        return float("nan")
    embeddings = model.encode(responses, show_progress_bar=False)
    sim_matrix = cosine_similarity(embeddings)
    # Upper triangle (excluding diagonal)
    n = len(responses)
    pairs = [(i, j) for i in range(n) for j in range(i + 1, n)]
    scores = [sim_matrix[i, j] for i, j in pairs]
    return float(np.mean(scores))


# ---------------------------------------------------------------------------
# Semantic Accuracy Score (SAS) — annotation reconciliation
# ---------------------------------------------------------------------------

def load_annotations() -> tuple[pd.DataFrame, pd.DataFrame]:
    rater_a = pd.read_csv(ANNOTATIONS_DIR / "rater_a.csv")
    rater_b = pd.read_csv(ANNOTATIONS_DIR / "rater_b.csv")
    return rater_a, rater_b


def compute_cohens_kappa(rater_a: list[int], rater_b: list[int]) -> float:
    return cohen_kappa_score(rater_a, rater_b)


def reconcile_sas(rater_a: pd.DataFrame, rater_b: pd.DataFrame) -> pd.DataFrame:
    """
    Merge rater annotations; use mean score for disagreements.
    Returns DataFrame with columns: function_id, attempt, sas_reconciled.
    """
    merged = rater_a.merge(
        rater_b,
        on=["function_id", "attempt"],
        suffixes=("_a", "_b"),
    )
    merged["sas_reconciled"] = (merged["sas_score_a"] + merged["sas_score_b"]) / 2
    kappa = compute_cohens_kappa(
        merged["sas_score_a"].tolist(),
        merged["sas_score_b"].tolist(),
    )
    log.info("Inter-rater Cohen's κ = %.4f", kappa)
    merged["cohens_kappa"] = kappa
    return merged[["function_id", "attempt", "sas_reconciled", "cohens_kappa"]]


# ---------------------------------------------------------------------------
# Main scorer
# ---------------------------------------------------------------------------

def run() -> pd.DataFrame:
    log.info("Loading raw LLM responses from %s", RAW_RESPONSES_CSV)
    responses_df = pd.read_csv(RAW_RESPONSES_CSV)

    log.info("Loading sentence transformer: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)

    # --- SCS per function ---
    scs_rows = []
    for func_id, group in responses_df.groupby("function_id"):
        texts = group["response_text"].tolist()
        scs = compute_scs(texts, model)
        mean_input_tokens = group["input_tokens"].mean()
        mean_output_tokens = group["output_tokens"].mean()
        scs_rows.append({
            "function_id": func_id,
            "scs": round(scs, 4),
            "mean_input_tokens": round(mean_input_tokens, 2),
            "mean_output_tokens": round(mean_output_tokens, 2),
            "output_input_ratio": round(mean_output_tokens / mean_input_tokens, 4)
                if mean_input_tokens > 0 else None,
        })

    scs_df = pd.DataFrame(scs_rows)

    # --- SAS (if annotations exist) ---
    rater_a_path = ANNOTATIONS_DIR / "rater_a.csv"
    rater_b_path = ANNOTATIONS_DIR / "rater_b.csv"
    rater_a_has_data = rater_a_path.stat().st_size > 30 and len(pd.read_csv(rater_a_path)) > 0
    rater_b_has_data = rater_b_path.stat().st_size > 30 and len(pd.read_csv(rater_b_path)) > 0
    if rater_a_has_data and rater_b_has_data:
        rater_a, rater_b = load_annotations()
        sas_df = reconcile_sas(rater_a, rater_b)
        sas_agg = sas_df.groupby("function_id")["sas_reconciled"].mean().reset_index()
        sas_agg.columns = ["function_id", "mean_sas"]
        results = scs_df.merge(sas_agg, on="function_id", how="left")
    else:
        log.warning(
            "Annotation files are empty — SAS will not be computed. "
            "Fill data/annotations/rater_a.csv and rater_b.csv after manual review."
        )
        results = scs_df
        results["mean_sas"] = float("nan")

    results.to_csv(EXP2_RESULTS, index=False)
    log.info("Comprehension scores written to %s", EXP2_RESULTS)
    return results


if __name__ == "__main__":
    run()
