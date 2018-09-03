import unittest
from unittest.mock import patch
from collections import defaultdict
from decimal import Decimal
from copy import copy
from exchange.binance import Binance
from internals.order import Order
from internals.enums import OrderAction, OrderType
from internals.orderbook import OrderBook
from rebalancer.limit_order_rebalancer import limit_order_rebalance
from rebalancer.limit_order_rebalancer import limit_order_rebalance_with_orders


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
        limit_order_rebalance('', exchange, weights)
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
        limit_order_rebalance('', exchange, weights)
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

    def test_limit_order_rebalance_with_orders(self):
        CopyFakeExchange = type('CopyFakeExchange',
                                FakeExchange.__bases__,
                                dict(FakeExchange.__dict__))

        def orderbooks_generator(orderbooks):
            for orderbook in orderbooks:
                yield orderbook

        def infinite_generator(x):
            while True:
                yield x

        def generator_to_function(generator):
            def _f(self):
                return next(generator)
            return _f

        def place_limit_order(self, order):
            self.order_id += 1
            self.orders[self.order_id] = copy(order)
            return {'order_id': self.order_id}
        CopyFakeExchange.place_limit_order = place_limit_order

        def cancel_limit_order(self, order):
            return
        CopyFakeExchange.cancel_limit_order = cancel_limit_order

        def get_order(self, order_response):
            q = self.orders[order_response['order_id']]._quantity
            return {'orig_quantity': q, 'executed_quantity': q}
        CopyFakeExchange.get_order = get_order

        resources = {
            'BTC': Decimal('1'),
            'ETH': Decimal('10'),
            'LTC': Decimal('100'),
            'USDT': Decimal('10000')
        }
        products = {'BTC_USDT', 'ETH_BTC', 'LTC_USDT', 'LTC_ETH'}

        orderbook_BTC_USDT1 = OrderBook('BTC_USDT', Decimal('10000'))
        orderbook_ETH_BTC1 = OrderBook('ETH_BTC', Decimal('0.1'))
        orderbook_LTC_USDT1 = OrderBook('LTC_USDT', Decimal('100'))
        orderbook_LTC_ETH1 = OrderBook('LTC_ETH', Decimal('0.1'))

        orderbook_BTC_USDT2 = OrderBook('BTC_USDT', Decimal('10000'))
        orderbook_ETH_BTC2 = OrderBook('ETH_BTC', Decimal('0.1'))
        orderbook_LTC_USDT2 = OrderBook('LTC_USDT', Decimal('98'))
        orderbook_LTC_ETH2 = OrderBook('LTC_ETH', Decimal('0.1'))

        orderbook_BTC_USDT3 = OrderBook('BTC_USDT', Decimal('10'))
        orderbook_ETH_BTC3 = OrderBook('ETH_BTC', Decimal('10000'))
        orderbook_LTC_USDT3 = OrderBook('LTC_USDT', Decimal('99'))
        orderbook_LTC_ETH3 = OrderBook('LTC_ETH', Decimal('0.001'))

        orderbooks1 = [orderbook_LTC_ETH1, orderbook_ETH_BTC1,
                       orderbook_BTC_USDT1, orderbook_LTC_USDT1]
        orderbooks1 = {ob.product: ob for ob in orderbooks1}

        orderbooks2 = [orderbook_LTC_ETH2, orderbook_ETH_BTC2,
                       orderbook_BTC_USDT2, orderbook_LTC_USDT2]
        orderbooks2 = {ob.product: ob for ob in orderbooks2}

        orderbooks3 = [orderbook_LTC_ETH3, orderbook_ETH_BTC3,
                       orderbook_BTC_USDT3, orderbook_LTC_USDT3]
        orderbooks3 = {ob.product: ob for ob in orderbooks3}

        orderbooks = [orderbooks1, orderbooks2, orderbooks3]

        orders = [Order('BTC_USDT', OrderType.LIMIT, OrderAction.SELL,
                        Decimal('1'), Decimal()),
                  Order('LTC_USDT', OrderType.LIMIT, OrderAction.BUY,
                        Decimal('200'), Decimal()),
                  Order('LTC_ETH', OrderType.LIMIT, OrderAction.BUY,
                        Decimal('100'), Decimal())]

        correct_orders = [Order('BTC_USDT', OrderType.LIMIT, OrderAction.SELL,
                                Decimal('1'), Decimal('10000')),
                          Order('LTC_ETH', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('100'), Decimal('0.1')),
                          Order('LTC_USDT', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('200'), Decimal('100'))]

        CopyFakeExchange.orderbooks = property(
            generator_to_function(infinite_generator(orderbooks1)), None, None,
            'orderbooks using generator')

        exchange = CopyFakeExchange(order_id=0, orders={})

        orders_copy = [copy(order) for order in orders]

        # no retry, but all orders are executed

        rets = limit_order_rebalance_with_orders(exchange, resources, products,
                                                 orders_copy, 0, 0)

        self.assertEqual(len(rets), 3)

        self.assertDictEqual(rets[0], {'orig_quantity': Decimal('1'),
                                       'executed_quantity': Decimal('1')})
        # 'BTC_USDT' it's first in orders list and it can be made
        self.assertDictEqual(rets[1], {'orig_quantity': Decimal('100'),
                                       'executed_quantity': Decimal('100')})
        # 'LTC_ETH' it's third in orders list and
        # but second can't be made at this time
        self.assertDictEqual(rets[2], {'orig_quantity': Decimal('200'),
                                       'executed_quantity': Decimal('200')})
        # 'LTC_USDT'

        self.assertEqual(len(exchange.orders), 3)

        for (order, correct_order) in zip([
                exchange.orders[i] for i in range(1, 4)],
                correct_orders):
            self.assertEqual(order.product, correct_order.product)
            self.assertEqual(order._type, correct_order._type)
            self.assertEqual(order._action, correct_order._action)
            self.assertEqual(order._quantity, correct_order._quantity)
            self.assertEqual(order._price, correct_order._price)

        def get_order(self, order_response):
            order_id = order_response['order_id']
            order = self.orders[order_id]
            q = order._quantity
            product = order.product
            if product == 'LTC_USDT' and order_id == 3:
                return {'orig_quantity': q, 'executed_quantity': q / 2}
            return {'orig_quantity': q, 'executed_quantity': q}
        CopyFakeExchange.get_order = get_order

        CopyFakeExchange.orderbooks = property(
            generator_to_function(
                orderbooks_generator(orderbooks)), None, None,
            'orderbooks using generator')

        exchange = CopyFakeExchange(order_id=0, orders={})

        orders_copy = [copy(order) for order in orders]

        # 1 retry available, so LTC is bought with USDT after 1 retry

        rets = limit_order_rebalance_with_orders(exchange, resources, products,
                                                 orders_copy, 1, 0)

        self.assertEqual(len(rets), 4)

        self.assertDictEqual(rets[0], {'orig_quantity': Decimal('1'),
                                       'executed_quantity': Decimal('1')})
        # 'BTC_USDT' it's first in orders list and it can be made
        self.assertDictEqual(rets[1], {'orig_quantity': Decimal('100'),
                                       'executed_quantity': Decimal('100')})
        # 'LTC_ETH' it's third in orders list and
        # but second can't be made at this time
        self.assertDictEqual(rets[2], {'orig_quantity': Decimal('200'),
                                       'executed_quantity': Decimal('100')})
        # 'LTC_USDT' first part

        self.assertDictEqual(rets[3], {'orig_quantity': Decimal('100'),
                                       'executed_quantity': Decimal('100')})
        # 'LTC_USDT' remaining

        correct_orders = [Order('BTC_USDT', OrderType.LIMIT, OrderAction.SELL,
                                Decimal('1'), Decimal('10000')),
                          Order('LTC_ETH', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('100'), Decimal('0.1')),
                          Order('LTC_USDT', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('200'), Decimal('98')),
                          Order('LTC_USDT', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('100'), Decimal('99'))]

        self.assertEqual(len(exchange.orders), 4)

        for (order, correct_order) in zip([
                exchange.orders[i] for i in range(1, 5)],
                correct_orders):
            self.assertEqual(order.product, correct_order.product)
            self.assertEqual(order._type, correct_order._type)
            self.assertEqual(order._action, correct_order._action)
            self.assertEqual(order._quantity, correct_order._quantity)
            self.assertEqual(order._price, correct_order._price)

        CopyFakeExchange.orderbooks = property(
            generator_to_function(
                orderbooks_generator(orderbooks)), None, None,
            'orderbooks using generator')

        exchange = CopyFakeExchange(order_id=0, orders={})

        orders_copy = [copy(order) for order in orders]

        # 0 retries, so LTC is not bought fully with USDT

        rets = limit_order_rebalance_with_orders(exchange, resources, products,
                                                 orders_copy, 0, 0)

        self.assertEqual(len(rets), 3)

        self.assertDictEqual(rets[0], {'orig_quantity': Decimal('1'),
                                       'executed_quantity': Decimal('1')})
        # 'BTC_USDT' it's first in orders list and it can be made
        self.assertDictEqual(rets[1], {'orig_quantity': Decimal('100'),
                                       'executed_quantity': Decimal('100')})
        # 'LTC_ETH' it's third in orders list and
        # but second can't be made at this time
        self.assertDictEqual(rets[2], {'orig_quantity': Decimal('200'),
                                       'executed_quantity': Decimal('100')})
        # 'LTC_USDT' first part

        correct_orders = [Order('BTC_USDT', OrderType.LIMIT, OrderAction.SELL,
                                Decimal('1'), Decimal('10000')),
                          Order('LTC_ETH', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('100'), Decimal('0.1')),
                          Order('LTC_USDT', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('200'), Decimal('98'))]

        self.assertEqual(len(exchange.orders), 3)

        for (order, correct_order) in zip([
                exchange.orders[i] for i in range(1, 4)],
                correct_orders):
            self.assertEqual(order.product, correct_order.product)
            self.assertEqual(order._type, correct_order._type)
            self.assertEqual(order._action, correct_order._action)
            self.assertEqual(order._quantity, correct_order._quantity)
            self.assertEqual(order._price, correct_order._price)

        def get_order(self, order_response):
            order_id = order_response['order_id']
            order = self.orders[order_id]
            q = order._quantity
            product = order.product
            if product == 'BTC_USDT' and order_id == 1:
                return {'orig_quantity': q, 'executed_quantity': 0}
            return {'orig_quantity': q, 'executed_quantity': q}
        CopyFakeExchange.get_order = get_order

        CopyFakeExchange.orderbooks = property(
            generator_to_function(
                orderbooks_generator(orderbooks)), None, None,
            'orderbooks using generator')

        exchange = CopyFakeExchange(order_id=0, orders={})

        orders_copy = [copy(order) for order in orders]

        # 0 retries, so BTC is not sold, but ETH is sold from first trial

        rets = limit_order_rebalance_with_orders(exchange, resources, products,
                                                 orders_copy, 0, 0)

        self.assertEqual(len(rets), 2)

        self.assertDictEqual(rets[0], {'orig_quantity': Decimal('1'),
                                       'executed_quantity': Decimal('0')})
        # 'BTC_USDT' it's first in orders list and it can be made
        self.assertDictEqual(rets[1], {'orig_quantity': Decimal('100'),
                                       'executed_quantity': Decimal('100')})

        correct_orders = [Order('BTC_USDT', OrderType.LIMIT, OrderAction.SELL,
                                Decimal('1'), Decimal('10000')),
                          Order('LTC_ETH', OrderType.LIMIT, OrderAction.BUY,
                                Decimal('100'), Decimal('0.1'))]

        self.assertEqual(len(exchange.orders), 2)

        for (order, correct_order) in zip([
                exchange.orders[i] for i in range(1, 3)],
                correct_orders):
            self.assertEqual(order.product, correct_order.product)
            self.assertEqual(order._type, correct_order._type)
            self.assertEqual(order._action, correct_order._action)
            self.assertEqual(order._quantity, correct_order._quantity)
            self.assertEqual(order._price, correct_order._price)


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
