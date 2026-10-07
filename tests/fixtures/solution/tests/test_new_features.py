from decimal import Decimal

from app.models import LineItem, Order
from app.pricing import tax


def test_tax_ny():
    assert tax(Order([LineItem("A", Decimal("10.00"), 1)], region="NY")) == Decimal("0.40")
