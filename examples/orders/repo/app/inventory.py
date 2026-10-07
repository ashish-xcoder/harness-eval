import logging

from app.errors import UnknownSku

logger = logging.getLogger(__name__)


class Inventory:
    def __init__(self, stock: dict[str, int]) -> None:
        self._stock = dict(stock)

    def available(self, sku: str) -> int:
        if sku not in self._stock:
            raise UnknownSku(sku)
        return self._stock[sku]
