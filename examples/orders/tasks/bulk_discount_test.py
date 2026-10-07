from decimal import Decimal

from app.models import LineItem, Order
from app.pricing import line_total, subtotal


def test_ten_units_get_five_percent_off():
    assert line_total(LineItem("A", Decimal("2.00"), 10)) == Decimal("19.00")


def test_nine_units_pay_full_price():
    assert line_total(LineItem("A", Decimal("2.00"), 9)) == Decimal("18.00")


def test_discount_rounds_half_up_to_cents():
    # 12 * 1.99 = 23.88 ; 5% off = 22.686 -> 22.69
    assert line_total(LineItem("A", Decimal("1.99"), 12)) == Decimal("22.69")


def test_subtotal_mixes_discounted_and_full_lines():
    order = Order([LineItem("A", Decimal("2.00"), 10), LineItem("B", Decimal("3.00"), 1)])
    assert subtotal(order) == Decimal("22.00")
