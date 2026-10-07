import logging
from decimal import ROUND_HALF_UP, Decimal

from app.models import LineItem, Order

logger = logging.getLogger(__name__)

CENT = Decimal("0.01")


def to_cents(amount: Decimal) -> Decimal:
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def line_total(item: LineItem) -> Decimal:
    return to_cents(item.unit_price * item.quantity)


def subtotal(order: Order) -> Decimal:
    total = sum((line_total(item) for item in order.items), Decimal("0"))
    logger.debug("subtotal for %d items: %s", len(order.items), total)
    return to_cents(total)
