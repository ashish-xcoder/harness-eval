class OrderError(Exception):
    """Base class for every domain error raised by the orders service."""


class InvalidQuantity(OrderError):
    """A line item was created with a quantity that is not a positive integer."""


class UnknownSku(OrderError):
    """The SKU is not known to the inventory."""
