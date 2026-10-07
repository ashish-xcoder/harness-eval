import logging

from app.errors import OutOfStock, UnknownSku
from app.models import LineItem

logger = logging.getLogger(__name__)


class Inventory:
    def __init__(self, stock: dict[str, int]) -> None:
        self._stock = dict(stock)

    def available(self, sku: str) -> int:
        if sku not in self._stock:
            raise UnknownSku(sku)
        return self._stock[sku]

    def reserve(self, items: list[LineItem]) -> None:
        needed: dict[str, int] = {}
        for item in items:
            needed[item.sku] = needed.get(item.sku, 0) + item.quantity
        for sku, qty in needed.items():
            if self.available(sku) < qty:
                raise OutOfStock(sku)
        for sku, qty in needed.items():
            self._stock[sku] -= qty
