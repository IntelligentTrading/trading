from decimal import Decimal


class OrderBook:
    def __init__(self, product: str, orderbook_from_market):
        assert len(product.split('_')) == 2
        self.product = product
        self.wall_ask = None
        self.wall_bid = None
        # TODO: parse orderbook from market

    def get_mid_market_price(self) -> Decimal:
        assert self.wall_ask is not None and self.wall_bid is not None
        return (self.wall_ask + self.wall_bid) / 2

    def get_wall_bid(self) -> Decimal:
        assert self.wall_bid is not None
        return self.wall_bid

    def get_wall_ask(self) -> Decimal:
        assert self.wall_ask is not None
        return self.wall_ask
