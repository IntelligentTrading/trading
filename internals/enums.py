from enum import Enum


class OrderAction(Enum):
    BUY = 1
    SELL = 2


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
