import unittest
from internals.orderbook import OrderBook


class OrderBookTester(unittest.TestCase):
    def test_order_book(self):
        orderbook1 = OrderBook('BTC_USDT', {'ask': 100, 'bid': 50})
        orderbook2 = OrderBook('BTC_USDT', [100, 50])
        orderbook3 = OrderBook('BTC_USDT', [50, 100])

        self.assertEqual(orderbook1.product, 'BTC_USDT')
        self.assertEqual(orderbook2.product, 'BTC_USDT')
        self.assertEqual(orderbook3.product, 'BTC_USDT')

        self.assertEqual(orderbook1.get_wall_ask(), 100)
        self.assertEqual(orderbook2.get_wall_ask(), 100)
        self.assertEqual(orderbook3.get_wall_ask(), 100)

        self.assertEqual(orderbook1.get_wall_bid(), 50)
        self.assertEqual(orderbook2.get_wall_bid(), 50)
        self.assertEqual(orderbook3.get_wall_bid(), 50)

        self.assertEqual(orderbook1.get_mid_market_price(), 75)

        orderbook = OrderBook('BTC_USDT', 10)

        self.assertEqual(orderbook.get_wall_ask(), 10)
        self.assertEqual(orderbook.get_wall_bid(), 10)
        self.assertEqual(orderbook.get_mid_market_price(), 10)
