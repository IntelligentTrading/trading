from decimal import Decimal


class OrderBook:
    def __init__(self, product: str, orderbook_from_market):
        assert len(product.split('_')) == 2
        self.product = product
        self.wall_ask = None
        self.wall_bid = None
        if type(orderbook_from_market) in [int, float, Decimal]:
            self.wall_ask = orderbook_from_market
            self.wall_bid = orderbook_from_market
        if type(orderbook_from_market) is dict:
            self.wall_bid = orderbook_from_market['bid']
            self.wall_ask = orderbook_from_market['ask']
        if type(orderbook_from_market) is list:
            assert len(orderbook_from_market) == 2
            self.wall_ask = max(orderbook_from_market)
            self.wall_bid = min(orderbook_from_market)

    def get_mid_market_price(self) -> Decimal:
        assert self.wall_ask is not None and self.wall_bid is not None
        return (self.wall_ask + self.wall_bid) / 2

    def get_wall_bid(self) -> Decimal:
        assert self.wall_bid is not None
        return self.wall_bid

    def get_wall_ask(self) -> Decimal:
        assert self.wall_ask is not None
        return self.wall_ask
