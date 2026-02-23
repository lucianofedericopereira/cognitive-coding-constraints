# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""Shared utilities: random seeds, paths, logging, caching."""

import os
import json
import hashlib
import logging
from pathlib import Path

# ---------------------------------------------------------------------------
# Reproducibility
# ---------------------------------------------------------------------------
RANDOM_SEED = 42

# ---------------------------------------------------------------------------
# Project paths
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
RESULTS_DIR = ROOT / "results"
CACHE_DIR = DATA_DIR / "cache"

SEED_CSV = DATA_DIR / "seed_identifiers.csv"
CORPUS_CSV = DATA_DIR / "extended_corpus.csv"
CODE_FUNCTIONS_DIR = DATA_DIR / "code_functions"
ANNOTATIONS_DIR = DATA_DIR / "annotations"

EXP1_RESULTS = RESULTS_DIR / "exp1_token_counts.csv"
EXP2_RESULTS = RESULTS_DIR / "exp2_comprehension_scores.csv"
EXP3_RESULTS = RESULTS_DIR / "exp3_rank_correlations.csv"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# API response cache
# ---------------------------------------------------------------------------
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def _cache_key(payload: dict) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=True)
    return hashlib.sha256(raw.encode()).hexdigest()


def cache_get(payload: dict):
    key = _cache_key(payload)
    path = CACHE_DIR / f"{key}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def cache_set(payload: dict, response: dict) -> None:
    key = _cache_key(payload)
    path = CACHE_DIR / f"{key}.json"
    with open(path, "w") as f:
        json.dump(response, f, ensure_ascii=True, indent=2)


# ---------------------------------------------------------------------------
# Misc helpers
# ---------------------------------------------------------------------------
def ensure_dirs() -> None:
    for d in [DATA_DIR, RESULTS_DIR, CACHE_DIR, CODE_FUNCTIONS_DIR, ANNOTATIONS_DIR]:
        d.mkdir(parents=True, exist_ok=True)