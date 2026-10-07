import logging
from decimal import ROUND_HALF_UP, Decimal

from app.errors import InvalidCoupon
from app.models import LineItem, Order

logger = logging.getLogger(__name__)

CENT = Decimal("0.01")
BULK_UNITS = 10
BULK_RATE = Decimal("0.95")
TAX_RATES = {"CA": Decimal("0.0725"), "NY": Decimal("0.04")}
FREE_SHIPPING_FROM = Decimal("50.00")
STANDARD_SHIPPING = Decimal("5.99")
EXPRESS_SURCHARGE = Decimal("10.00")


def to_cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(item: LineItem) -> Decimal:
    total = item.unit_price * item.quantity
    if item.quantity >= BULK_UNITS:
        total *= BULK_RATE
    return to_cents(total)


def subtotal(order: Order) -> Decimal:
    total = sum((line_total(item) for item in order.items), Decimal("0"))
    logger.debug("subtotal for %d items: %s", len(order.items), total)
    return to_cents(total)


def apply_coupon(order: Order, code: str) -> Decimal:
    amount = subtotal(order)
    if code == "SAVE10":
        return to_cents(amount * Decimal("0.9"))
    if code == "FLAT5":
        return max(amount - Decimal("5.00"), Decimal("0.00"))
    raise InvalidCoupon(code)


def tax(order: Order) -> Decimal:
    return to_cents(subtotal(order) * TAX_RATES.get(order.region, Decimal("0")))


def shipping_cost(order: Order, express: bool = False) -> Decimal:
    cost = Decimal("0.00") if subtotal(order) >= FREE_SHIPPING_FROM else STANDARD_SHIPPING
    return cost + (EXPRESS_SURCHARGE if express else Decimal("0"))
