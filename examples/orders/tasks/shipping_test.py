from decimal import Decimal

from app.models import LineItem, Order
from app.pricing import shipping_cost


def order_of(amount: str) -> Order:
    return Order([LineItem("A", Decimal(amount), 1)])


def test_standard_shipping_under_threshold():
    assert shipping_cost(order_of("49.99")) == Decimal("5.99")


def test_free_shipping_at_threshold():
    assert shipping_cost(order_of("50.00")) == Decimal("0.00")


def test_express_adds_ten_dollars():
    assert shipping_cost(order_of("20.00"), express=True) == Decimal("15.99")
    assert shipping_cost(order_of("80.00"), express=True) == Decimal("10.00")
