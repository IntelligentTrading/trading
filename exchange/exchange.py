from internals.order import Order


class Exchange:
    def __init__(self):
        pass

    def get_orderbooks(self, depth: int =1):
        # products in 'commodity_base' format
        raise NotImplementedError

    def get_resources(self):
        raise NotImplementedError

    def place_market_order(self, order: Order):
        raise NotImplementedError

    def place_limit_order(self, order: Order):
        raise NotImplementedError

    def cancel_limit_order(self, **params):
        raise NotImplementedError

    def get_order(self, **params):
        raise NotImplementedError

    def get_taker_fee(self, product):
        raise NotImplementedError

    def get_maker_fee(self, product):
        raise NotImplementedError

    def through_trade_currencies(self):
        raise NotImplementedError
