from enum import Enum


class OrderSide(Enum):
    BID = 1
    ASK = 2


class OrderType(Enum):
    MARKET = 1
    LIMIT = 2
