from decimal import Decimal

import pytest

from app.errors import InvalidQuantity, OrderError
from app.models import LineItem, Order
from app.pricing import line_total, subtotal


def test_line_total_multiplies_price_by_quantity():
    assert line_total(LineItem("A", Decimal("2.50"), 3)) == Decimal("7.50")


def test_subtotal_sums_lines():
    order = Order([LineItem("A", Decimal("2.50"), 2), LineItem("B", Decimal("1.25"), 1)])
    assert subtotal(order) == Decimal("6.25")


def test_empty_order_subtotal_is_zero():
    assert subtotal(Order()) == Decimal("0.00")


def test_non_positive_quantity_is_rejected():
    with pytest.raises(InvalidQuantity):
        LineItem("A", Decimal("1.00"), 0)
    assert issubclass(InvalidQuantity, OrderError)
