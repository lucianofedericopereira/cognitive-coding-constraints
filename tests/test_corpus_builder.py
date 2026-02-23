"""Unit tests for corpus_builder.py notation converters."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from corpus_builder import to_dot, to_camel, to_snake, to_kebab


def test_to_dot_simple():
    assert to_dot("order created") == "order.created"


def test_to_dot_multiword():
    assert to_dot("payment refund initiated") == "payment.refund.initiated"


def test_to_camel_simple():
    assert to_camel("order created") == "orderCreated"


def test_to_camel_multiword():
    assert to_camel("payment refund initiated") == "paymentRefundInitiated"


def test_to_snake_simple():
    assert to_snake("order created") == "order_created"


def test_to_kebab_simple():
    assert to_kebab("order created") == "order-created"


def test_no_leading_trailing_whitespace():
    assert to_dot("  order created  ") == "order.created"
    assert to_camel("  order created  ") == "orderCreated"
