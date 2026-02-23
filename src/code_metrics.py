# -----------------------------------------------------------------------------
# Author:  Luciano Federico Pereira
# ORCID:   https://orcid.org/0009-0002-4591-6568
# Paper:   Empirical Validation of Cognitive-Derived Coding Constraints and
#          Tokenization Asymmetries in LLM-Assisted Software Engineering
# Repo:    https://github.com/lucianofedericopereira/cognitive-coding-constraints
# License: LGPL-2.1
# -----------------------------------------------------------------------------

"""
code_metrics.py — Experiment 2: structural metrics for code corpus.

For each .py file in data/code_functions/, computes CDCC-relevant
metrics and writes a summary CSV consumed by llm_probe.py and
changepoint_analysis.py.

Dependencies: radon, ast (stdlib)
"""

import ast
import textwrap
from pathlib import Path

import pandas as pd
import radon.complexity as rc
import radon.metrics as rm
from radon.visitors import ComplexityVisitor

from utils import CODE_FUNCTIONS_DIR, get_logger

log = get_logger(__name__)

# ---------------------------------------------------------------------------
# CDCC thresholds (from Pereira 2026b, Table 2)
# ---------------------------------------------------------------------------
CDCC_MAX_COMPLEXITY = 10
CDCC_MAX_LOC = 50
CDCC_MAX_NESTING = 4
CDCC_MAX_ARGS = 7   # Miller's Law applied to function signature


# ---------------------------------------------------------------------------
# Metric extractors
# ---------------------------------------------------------------------------

def get_complexity(source: str) -> int:
    """McCabe cyclomatic complexity (max over all blocks in file)."""
    try:
        blocks = rc.cc_visit(source)
        return max((b.complexity for b in blocks), default=1)
    except Exception:
        return -1


def get_loc(source: str) -> int:
    """Logical lines of code (non-blank, non-comment)."""
    try:
        raw = rm.mi_visit(source, multi=True)
        # radon mi_visit returns MI score; use line-count directly
        lines = [l for l in source.splitlines() if l.strip() and not l.strip().startswith("#")]
        return len(lines)
    except Exception:
        return len([l for l in source.splitlines() if l.strip()])


def _nesting_depth(node: ast.AST, current: int = 0) -> int:
    """Recursively walk AST and return max nesting depth."""
    NESTING_NODES = (ast.For, ast.While, ast.If, ast.With, ast.Try,
                     ast.AsyncFor, ast.AsyncWith)
    max_depth = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, NESTING_NODES):
            max_depth = max(max_depth, _nesting_depth(child, current + 1))
        else:
            max_depth = max(max_depth, _nesting_depth(child, current))
    return max_depth


def get_nesting_depth(source: str) -> int:
    """Maximum control-flow nesting depth via AST walk."""
    try:
        tree = ast.parse(textwrap.dedent(source))
        return _nesting_depth(tree)
    except SyntaxError:
        return -1


def get_arg_count(source: str) -> int:
    """Number of arguments of the first function defined in source."""
    try:
        tree = ast.parse(textwrap.dedent(source))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return len(node.args.args)
        return 0
    except SyntaxError:
        return -1


def is_cdcc_compliant(metrics: dict) -> bool:
    return (
        metrics["complexity"] <= CDCC_MAX_COMPLEXITY
        and metrics["loc"] <= CDCC_MAX_LOC
        and metrics["nesting_depth"] <= CDCC_MAX_NESTING
    )


# ---------------------------------------------------------------------------
# Corpus scanner
# ---------------------------------------------------------------------------

def compute_metrics_for_file(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    metrics = {
        "function_id": path.stem,
        "file_path": str(path),
        "complexity": get_complexity(source),
        "loc": get_loc(source),
        "nesting_depth": get_nesting_depth(source),
        "arg_count": get_arg_count(source),
    }
    metrics["cdcc_violation"] = not is_cdcc_compliant(metrics)
    return metrics


def run() -> pd.DataFrame:
    files = sorted(CODE_FUNCTIONS_DIR.glob("*.py"))
    if not files:
        log.warning("No .py files found in %s", CODE_FUNCTIONS_DIR)
        return pd.DataFrame()

    log.info("Computing metrics for %d functions …", len(files))
    rows = [compute_metrics_for_file(f) for f in files]
    df = pd.DataFrame(rows)

    out = CODE_FUNCTIONS_DIR.parent / "code_metrics.csv"
    df.to_csv(out, index=False)
    log.info("Metrics written to %s", out)

    compliant = (~df["cdcc_violation"]).sum()
    log.info("CDCC-compliant: %d / %d", compliant, len(df))
    return df


if __name__ == "__main__":
    run()