# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
tokenizer_analysis.py — Experiment 1: multi-tokenizer token counting.

Loads the extended corpus, encodes each notation variant with each
tokenizer in the test matrix, computes efficiency metrics, and writes
results/exp1_token_counts.csv.

Statistical test: Wilcoxon signed-rank on paired (dot, camelCase) token
counts to replicate the 1.67x theoretical claim from Pereira (2026a).

Requires: tiktoken, transformers (plus model downloads on first run).
HF models are loaded lazily; set HF_TOKEN env var if gating applies.
"""

import os
import warnings
import numpy as np
import pandas as pd
import tiktoken
from scipy.stats import wilcoxon
from utils import CORPUS_CSV, EXP1_RESULTS, get_logger, RANDOM_SEED

log = get_logger(__name__)

NOTATION_COLS = ["dot", "camelCase", "snake_case", "kebab_case"]

# ---------------------------------------------------------------------------
# Tokenizer registry
# ---------------------------------------------------------------------------

def _load_tokenizers() -> dict:
    tokenizers = {}

    log.info("Loading tiktoken encodings …")
    tokenizers["gpt4o"] = tiktoken.get_encoding("o200k_base")
    tokenizers["gpt4"] = tiktoken.get_encoding("cl100k_base")
    # cl100k_base also used as Claude proxy (documented limitation)
    tokenizers["claude_proxy"] = tiktoken.get_encoding("cl100k_base")

    log.info("Loading HuggingFace tokenizers …")
    try:
        from transformers import AutoTokenizer
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            tokenizers["llama3"] = AutoTokenizer.from_pretrained(
                "meta-llama/Meta-Llama-3-8B",
                token=os.getenv("HF_TOKEN"),
            )
            tokenizers["mistral"] = AutoTokenizer.from_pretrained(
                "mistralai/Mistral-7B-v0.1",
                token=os.getenv("HF_TOKEN"),
            )
    except Exception as e:
        log.warning("Could not load HF tokenizers (%s). Skipping.", e)

    return tokenizers


def count_tokens(text: str, tokenizer) -> int:
    """Return token count for *text* using *tokenizer* (tiktoken or HF)."""
    if hasattr(tokenizer, "encode"):
        encoded = tokenizer.encode(text)
        # tiktoken returns list; HF returns list or BatchEncoding
        if hasattr(encoded, "input_ids"):
            return len(encoded.input_ids)
        return len(encoded)
    raise TypeError(f"Unknown tokenizer type: {type(tokenizer)}")


# ---------------------------------------------------------------------------
# Core analysis
# ---------------------------------------------------------------------------

def compute_token_counts(df: pd.DataFrame, tokenizers: dict) -> pd.DataFrame:
    rows = []
    for _, row in df.iterrows():
        for tok_name, tok in tokenizers.items():
            entry = {
                "id": row["id"],
                "semantic_form": row["semantic_form"],
                "domain": row["domain"],
                "tokenizer": tok_name,
            }
            word_count = len(row["semantic_form"].split())
            for notation in NOTATION_COLS:
                n = count_tokens(row[notation], tok)
                entry[f"{notation}_tokens"] = n
                entry[f"{notation}_efficiency"] = round(word_count / n, 4) if n > 0 else None
            rows.append(entry)
    return pd.DataFrame(rows)


def compute_ratio(df: pd.DataFrame, base: str = "dot", target: str = "camelCase") -> pd.DataFrame:
    col = f"{base}_vs_{target}_ratio"
    df[col] = df[f"{base}_tokens"] / df[f"{target}_tokens"]
    return df


def run_wilcoxon(df: pd.DataFrame, tokenizer_name: str) -> dict:
    sub = df[df["tokenizer"] == tokenizer_name].copy()
    stat, p = wilcoxon(sub["dot_tokens"], sub["camelCase_tokens"])
    mean_ratio = (sub["dot_tokens"] / sub["camelCase_tokens"]).mean()
    return {
        "tokenizer": tokenizer_name,
        "mean_dot_vs_camel_ratio": round(mean_ratio, 4),
        "wilcoxon_stat": round(stat, 4),
        "p_value": round(p, 6),
        "significant": p < 0.05,
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def run() -> pd.DataFrame:
    log.info("Loading corpus from %s", CORPUS_CSV)
    df = pd.read_csv(CORPUS_CSV)

    tokenizers = _load_tokenizers()

    log.info("Computing token counts for %d identifiers × %d tokenizers …",
             len(df), len(tokenizers))
    results = compute_token_counts(df, tokenizers)
    results = compute_ratio(results)

    results.to_csv(EXP1_RESULTS, index=False)
    log.info("Results written to %s", EXP1_RESULTS)

    log.info("\n=== Wilcoxon signed-rank tests (dot vs camelCase) ===")
    for tok_name in tokenizers:
        stats = run_wilcoxon(results, tok_name)
        log.info(
            "%s  ratio=%.4f  W=%.2f  p=%.6f  significant=%s",
            stats["tokenizer"], stats["mean_dot_vs_camel_ratio"],
            stats["wilcoxon_stat"], stats["p_value"], stats["significant"],
        )

    return results


if __name__ == "__main__":
    run()