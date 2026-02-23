"""Unit tests for code_metrics.py structural metric extractors."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from code_metrics import (
    get_complexity, get_loc, get_nesting_depth, get_arg_count, is_cdcc_compliant
)

SIMPLE_FUNCTION = """\
def add(a, b):
    return a + b
"""

NESTED_FUNCTION = """\
def deeply_nested(x):
    if x > 0:
        for i in range(x):
            while i > 0:
                if i % 2 == 0:
                    i -= 1
    return x
"""

COMPLEX_FUNCTION = """\
def complex_fn(a, b, c, d, e):
    if a:
        if b:
            if c:
                if d:
                    return e
            elif e:
                return d
        else:
            return c
    elif b:
        for i in range(10):
            if i % 2:
                continue
        return a
    return None
"""


def test_simple_complexity():
    cc = get_complexity(SIMPLE_FUNCTION)
    assert cc == 1


def test_simple_loc():
    loc = get_loc(SIMPLE_FUNCTION)
    assert loc >= 1


def test_simple_arg_count():
    assert get_arg_count(SIMPLE_FUNCTION) == 2


def test_nesting_depth_nested():
    depth = get_nesting_depth(NESTED_FUNCTION)
    assert depth >= 4


def test_cdcc_compliant_simple():
    metrics = {
        "complexity": 1,
        "loc": 2,
        "nesting_depth": 0,
    }
    assert is_cdcc_compliant(metrics) is True


def test_cdcc_violation_complexity():
    metrics = {
        "complexity": 15,
        "loc": 30,
        "nesting_depth": 2,
    }
    assert is_cdcc_compliant(metrics) is False


def test_cdcc_violation_nesting():
    metrics = {
        "complexity": 5,
        "loc": 20,
        "nesting_depth": 5,
    }
    assert is_cdcc_compliant(metrics) is False
