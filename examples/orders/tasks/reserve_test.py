from decimal import Decimal

import pytest

from app.inventory import Inventory
from app.models import LineItem


def item(sku: str, qty: int) -> LineItem:
    return LineItem(sku, Decimal("1.00"), qty)


def test_reserve_decrements_stock():
    inv = Inventory({"A": 5, "B": 2})
    inv.reserve([item("A", 3), item("B", 2)])
    assert inv.available("A") == 2
    assert inv.available("B") == 0


def test_insufficient_stock_is_rejected():
    inv = Inventory({"A": 1})
    with pytest.raises(Exception):
        inv.reserve([item("A", 2)])


def test_failed_reservation_changes_nothing():
    inv = Inventory({"A": 5, "B": 1})
    with pytest.raises(Exception):
        inv.reserve([item("A", 3), item("B", 2)])
    assert inv.available("A") == 5
    assert inv.available("B") == 1


def test_unknown_sku_is_rejected_without_side_effects():
    inv = Inventory({"A": 5})
    with pytest.raises(Exception):
        inv.reserve([item("A", 1), item("Z", 1)])
    assert inv.available("A") == 5
