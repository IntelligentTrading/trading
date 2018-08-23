import unittest
from exchange.binance import Binance


class BinanceTester(unittest.TestCase):
    def test_get_mid_price_orderbooks(self):
        binance = Binance()
        products = ['BTC_USDT', 'ETH_USDT']
        orderbooks = binance.get_mid_price_orderbooks(products)
        self.assertEqual(len(orderbooks), len(products))
        self.assertIn(orderbooks[0].product, products)
        self.assertIn(orderbooks[1].product, products)

    def test_get_orderbooks(self):
        binance = Binance()
        products = ['BTC_USDT', 'ETH_USDT']
        orderbooks = binance.get_orderbooks(products)
        self.assertEqual(len(orderbooks), len(products))
        self.assertIn(orderbooks[0].product, products)
        self.assertIn(orderbooks[1].product, products)
        self.assertLess(orderbooks[0].wall_bid, orderbooks[0].wall_ask)
        self.assertLess(orderbooks[1].wall_bid, orderbooks[1].wall_ask)
