import tests.webserver.init_django  # noqa
import unittest
from decimal import Decimal

from exchange import Exchange
from internals.orderbook import OrderBook
from webserver.views import get_portfolio


class DummyExchange(Exchange):
    def get_resources(self):
        return {"BTC": Decimal("1"),
                "ETH": Decimal("5"),
                "BNB": Decimal("1000")}

    def get_orderbooks(self, depth: int =1):
        return [OrderBook("ETH_BTC", [Decimal("0.2")] * 2),
                OrderBook("BNB_BTC", [Decimal("0.001")] * 2)]


class ViewsTester(unittest.TestCase):

    def test_get_portfolio(self):
        exchange = DummyExchange()
        portfolio = get_portfolio(exchange)

        self.assertDictEqual(portfolio, {
            "value": Decimal("3"),
            "allocations": [
                {
                    "coin": "BTC",
                    "amount": Decimal("1"),
                    "portion": Decimal("0.3333")
                }, {
                    "coin": "ETH",
                    "amount": Decimal("5"),
                    "portion": Decimal("0.3333")
                }, {
                    "coin": "BNB",
                    "amount": Decimal("1000"),
                    "portion": Decimal("0.3333")
                }]
        })
