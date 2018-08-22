from internals.order import Order


class Exchange:
    def __init__(self):
        pass

    def get_order_book(self, depth: int =1):
        raise NotImplementedError

    def get_resources(self):
        raise NotImplementedError

    def place_market_order(self, order: Order):
        raise NotImplementedError

    def place_limit_order(self, order: Order):
        raise NotImplementedError
