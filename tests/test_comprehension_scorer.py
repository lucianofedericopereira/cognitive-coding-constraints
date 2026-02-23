"""Unit tests for comprehension_scorer.py SCS computation."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def test_scs_identical_responses():
    from sentence_transformers import SentenceTransformer
    from comprehension_scorer import compute_scs

    model = SentenceTransformer("all-MiniLM-L6-v2")
    responses = ["This function adds two numbers."] * 5
    scs = compute_scs(responses, model)
    # Identical sentences should have SCS very close to 1.0
    assert scs > 0.99


def test_scs_different_responses():
    from sentence_transformers import SentenceTransformer
    from comprehension_scorer import compute_scs

    model = SentenceTransformer("all-MiniLM-L6-v2")
    responses = [
        "This function sorts a list.",
        "This function connects to a database.",
        "This function computes the factorial of a number.",
        "This function parses a JSON string.",
        "This function sends an HTTP request.",
    ]
    scs = compute_scs(responses, model)
    assert 0.0 <= scs <= 1.0


def test_scs_single_response():
    from sentence_transformers import SentenceTransformer
    from comprehension_scorer import compute_scs
    import math

    model = SentenceTransformer("all-MiniLM-L6-v2")
    scs = compute_scs(["Only one response."], model)
    assert math.isnan(scs)
