from exchange.exchange import Exchange
from internals.orderbook import OrderBook
from internals.utils import binance_product_to_currencies
from decimal import Decimal
from binance.client import Client


class Binance(Exchange):
    def __init__(self, api_key: str=None, secret_key: str=None):
        super().__init__()
        self.client = Client(api_key, secret_key)

    def get_mid_price_orderbooks(self, products=None):
        prices_list = self.client.get_all_tickers()
        orderbooks = []
        for price_symbol in prices_list:
            currency_pair = binance_product_to_currencies(
                price_symbol['symbol'])
            product = '_'.join(currency_pair)
            if products is not None and product not in products:
                continue
            orderbook = OrderBook(
                product, Decimal(price_symbol['price']))
            orderbooks.append(orderbook)
        return orderbooks

    def get_orderbooks(self, products=None, depth: int=1):
        if depth != 1:
            raise NotImplementedError
        return self.get_orderbooks_of_depth1(products)

    def get_orderbooks_of_depth1(self, products):
        books_list = self.client.get_orderbook_tickers()
        orderbooks = []
        for book in books_list:
            currency_pair = binance_product_to_currencies(
                book['symbol'])
            product = '_'.join(currency_pair)
            if products is not None and product not in products:
                continue
            orderbook = OrderBook(
                product, {'ask': Decimal(book['askPrice']),
                          'bid': Decimal(book['bidPrice'])})
            orderbooks.append(orderbook)
        return orderbooks
