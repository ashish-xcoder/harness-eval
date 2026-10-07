import pytest

from app.errors import UnknownSku
from app.inventory import Inventory


def test_available_returns_stock():
    assert Inventory({"A": 5}).available("A") == 5


def test_unknown_sku_raises():
    with pytest.raises(UnknownSku):
        Inventory({}).available("missing")
