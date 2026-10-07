from decimal import Decimal

from app.models import LineItem, Order
from app.pricing import tax


def order_in(region: str, amount: str = "10.00") -> Order:
    return Order([LineItem("A", Decimal(amount), 1)], region=region)


def test_california_rate_rounds_half_up():
    assert tax(order_in("CA")) == Decimal("0.73")


def test_new_york_rate():
    assert tax(order_in("NY")) == Decimal("0.40")


def test_other_regions_pay_no_tax():
    assert tax(order_in("TX")) == Decimal("0.00")
    assert tax(Order([LineItem("A", Decimal("10.00"), 1)])) == Decimal("0.00")


def test_tax_is_on_subtotal():
    order = Order([LineItem("A", Decimal("5.00"), 2), LineItem("B", Decimal("2.50"), 4)], region="NY")
    assert tax(order) == Decimal("0.80")
