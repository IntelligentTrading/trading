from decimal import Decimal


class OrderBook:
    def __init__(self, product: str, orderbook_from_market):
        self.product = product
        raise NotImplementedError

    def get_mid_market_price(self) -> Decimal:
        raise NotImplementedError

    def get_wall_bid(self) -> Decimal:
        raise NotImplementedError

    def get_wall_ask(self) -> Decimal:
        raise NotImplementedError
