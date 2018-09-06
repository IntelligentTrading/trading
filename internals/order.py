from internals.enums import OrderType, OrderAction
from decimal import Decimal


class Order:
    def __init__(self, product: str, _type: OrderType, _action: OrderAction,
                 quantity: Decimal, price: Decimal=None):
        self.product = product
        self._type = _type
        self._action = _action
        self._quantity = quantity
        self._price = price
        if self._price is None:
            assert self._type is OrderType.MARKET, (
                'price is required for limit orders')

    def __str__(self):
        s = ("<Order at {id}: [product={product}, type={type},"
             " action={action}, quantity={quantity}, price={price}]".format(
                 id=id(self), product=self.product, type=self._type,
                 action=self._action, quantity=self._quantity,
                 price=(self._price if self._price is not None else "None")))
        return s
