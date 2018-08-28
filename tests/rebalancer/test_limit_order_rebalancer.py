import unittest
from unittest.mock import patch
from collections import defaultdict
from decimal import Decimal

from exchange.binance import Binance
from internals.enums import OrderAction
from internals.orderbook import OrderBook
from rebalancer.limit_order_rebalancer import limit_order_rebalance


class LimitOrderRebalancerTester(unittest.TestCase):
    @patch('rebalancer.limit_order_rebalancer'
           '.limit_order_rebalance_with_orders')
    def test_limit_order_rebalance(self, function):
        resources = {
            'BTC': Decimal('1'),
            'ETH': Decimal('10'),
            'LTC': Decimal('100'),
            'USDT': Decimal('10000')
        }
        through_trade_currencies = {'USDT', 'BTC', 'ETH'}

        orderbook_BTC_USDT = OrderBook('BTC_USDT', Decimal('10000'))
        orderbook_ETH_BTC = OrderBook('ETH_BTC', Decimal('0.1'))
        orderbook_LTC_USDT = OrderBook('LTC_USDT', Decimal('100'))
        orderbook_LTC_ETH = OrderBook('LTC_ETH', Decimal('0.1'))
        orderbooks = [orderbook_LTC_ETH, orderbook_ETH_BTC,
                      orderbook_BTC_USDT, orderbook_LTC_USDT]

        fees = defaultdict(lambda: Decimal('0.001'))

        exchange = FakeExchange(
            resources=resources,
            _through_trade_currencies=through_trade_currencies,
            orderbooks=orderbooks, fees=fees)

        weights = {
            'LTC': Decimal('1')
        }

        fees['BTC_USDT'] = Decimal('0.0005')
        limit_order_rebalance(exchange, weights)
        (arg_exchange, arg_resources, arg_products,
         arg_orders, _, _), _ = function.call_args

        self.assertEqual(arg_exchange, exchange)
        self.assertDictEqual(resources, arg_resources)
        self.assertEqual(sorted(arg_products),
                         sorted('BTC_USDT ETH_BTC LTC_USDT LTC_ETH'.split()))

        arg_orders = sorted([(order.product, order._action, order._quantity)
                             for order in arg_orders])
        correct_orders = sorted([
            ('BTC_USDT', OrderAction.SELL, Decimal('1')),
            ('LTC_USDT', OrderAction.BUY, Decimal('200')),
            ('LTC_ETH', OrderAction.BUY, Decimal('100'))
        ])
        for order, correct_order in zip(arg_orders, correct_orders):
            self.assertEqual(order[0], correct_order[0])
            self.assertEqual(order[1], correct_order[1])
            self.assertEqual(order[2], correct_order[2])
        fees.pop('BTC_USDT')
        fees['ETH_BTC'] = Decimal('0.0005')
        correct_orders = sorted([
            ('ETH_BTC', OrderAction.BUY, Decimal('10')),
            ('LTC_USDT', OrderAction.BUY, Decimal('100')),
            ('LTC_ETH', OrderAction.BUY, Decimal('200'))
        ])
        limit_order_rebalance(exchange, weights)
        (arg_exchange, arg_resources, arg_products,
         arg_orders, _, _), _ = function.call_args

        self.assertEqual(arg_exchange, exchange)
        self.assertDictEqual(resources, arg_resources)
        self.assertEqual(sorted(arg_products),
                         sorted('BTC_USDT ETH_BTC LTC_USDT LTC_ETH'.split()))

        arg_orders = sorted([(order.product, order._action, order._quantity)
                             for order in arg_orders])
        for order, correct_order in zip(arg_orders, correct_orders):
            self.assertEqual(order[0], correct_order[0])
            self.assertEqual(order[1], correct_order[1])
            self.assertEqual(order[2], correct_order[2])


class FakeExchange(Binance):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_resources(self):
        return self.resources

    def through_trade_currencies(self):
        return self._through_trade_currencies

    def get_orderbooks(self, products):
        return self.orderbooks

    def get_maker_fee(self, product):
        return self.fees[product]
