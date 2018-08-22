from exchange.exchange import Exchange


class Gdax(Exchange):
    def __init__(self, api_key: str, secret_key: str):
        super().__init__()
        # TODO: initialize market
        raise NotImplementedError
