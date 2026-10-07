from dataclasses import dataclass, field
from decimal import Decimal

from app.errors import InvalidQuantity


@dataclass(frozen=True)
class LineItem:
    sku: str
    unit_price: Decimal
    quantity: int

    def __post_init__(self) -> None:
        if self.quantity <= 0:
            raise InvalidQuantity(f"quantity must be positive, got {self.quantity}")


@dataclass
class Order:
    items: list[LineItem] = field(default_factory=list)
    region: str = "default"
