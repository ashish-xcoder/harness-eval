from decimal import Decimal

import pytest

from app.models import LineItem, Order
from app.pricing import apply_coupon


def order_of(amount: str) -> Order:
    return Order([LineItem("A", Decimal(amount), 1)])


def test_save10_takes_ten_percent_off():
    assert apply_coupon(order_of("40.00"), "SAVE10") == Decimal("36.00")


def test_save10_rounds_to_cents():
    assert apply_coupon(order_of("10.05"), "SAVE10") == Decimal("9.05")


def test_flat5_takes_five_dollars_off():
    assert apply_coupon(order_of("12.00"), "FLAT5") == Decimal("7.00")


def test_flat5_never_goes_below_zero():
    assert apply_coupon(order_of("3.00"), "FLAT5") == Decimal("0.00")


def test_unknown_coupon_is_rejected():
    with pytest.raises(Exception):
        apply_coupon(order_of("10.00"), "BOGUS")
