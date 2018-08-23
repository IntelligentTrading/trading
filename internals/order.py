from internals.enums import OrderType, OrderSide
from decimal import Decimal


class Order:
    def __init__(self, product: str, _type: OrderType, _side: OrderSide,
                 quantity: Decimal, price: Decimal=None):
        self.product = product
        self._type = _type
        self._side = _side
        self._quantity = quantity
        self._price = price
        if self._price is None:
            assert self._type is OrderType.MARKET, (
                'price is required for limit orders')
