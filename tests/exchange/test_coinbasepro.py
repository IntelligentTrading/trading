import unittest
from decimal import Decimal
from internals.order import Order
from internals.enums import OrderType, OrderAction
from exchange.coinbasepro import CoinbasePro


class CoinbaseProTester(unittest.TestCase):
    def test_validate_order(self):
        resources = {
            'BTC': Decimal('1'),
            'USD': Decimal('100000')
        }
        filters = {
            'BTC-USD': {
                'min_order_size': Decimal('0.001'),
                'max_order_size': Decimal('10000'),
                'order_step': Decimal('1e-8'),
                'price_step': Decimal('0.01'),
                'base': 'USD',
                'commodity': 'BTC'
            }
        }
        price_estimates = {
            'BTC': Decimal('10000'),
            'USD': Decimal('1')
        }
        exchange = FakeExchange(resources=resources, filters=filters)

        # no change
        order = Order('BTC_USD', OrderType.MARKET,
                      OrderAction.SELL, Decimal('1'))
        correct_order = Order('BTC_USD', OrderType.MARKET,
                              OrderAction.SELL, Decimal('1'))
        order = exchange._validate_order(order, price_estimates)
        self.assertOrderEqual(order, correct_order)

        # less than min order size
        order = Order('BTC_USD', OrderType.MARKET,
                      OrderAction.SELL, Decimal('0.0001'))
        order = exchange._validate_order(order, price_estimates)
        self.assertIsNone(order)

        # morder than reources[commodity]
        order = Order('BTC_USD', OrderType.MARKET,
                      OrderAction.SELL, Decimal('2'))
        correct_order = Order('BTC_USD', OrderType.MARKET,
                              OrderAction.SELL, Decimal('1'))
        order = exchange._validate_order(order, price_estimates)
        self.assertOrderEqual(order, correct_order)

        # more than resources[base] taking in account fee
        order = Order('BTC_USD', OrderType.MARKET,
                      OrderAction.BUY, Decimal('10'))
        correct_order = Order('BTC_USD', OrderType.MARKET,
                              OrderAction.BUY, Decimal('9.97'))
        order = exchange._validate_order(order, price_estimates)
        self.assertLessEqual(order._quantity, correct_order._quantity)
        order._quantity = Decimal('0')
        correct_order._quantity = Decimal('0')
        self.assertOrderEqual(order, correct_order)

        # precision is too high
        order = Order('BTC_USD', OrderType.MARKET,
                      OrderAction.SELL, Decimal('0.999999999'))
        correct_order = Order('BTC_USD', OrderType.MARKET,
                              OrderAction.SELL, Decimal('0.99999999'))
        order = exchange._validate_order(order, price_estimates)
        self.assertOrderEqual(order, correct_order)

        # Limit order, no change
        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.SELL, Decimal('1'), Decimal('1000'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.SELL, Decimal('1'), Decimal('1000'))
        order = exchange._validate_order(order)
        self.assertOrderEqual(order, correct_order)

        # price precision SELL
        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.SELL, Decimal('1'), Decimal('1000.001'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.SELL, Decimal('1'),
                              Decimal('1000.01'))
        order = exchange._validate_order(order)
        self.assertOrderEqual(order, correct_order)

        # price precision BUY
        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.BUY, Decimal('1'), Decimal('1000.001'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.BUY, Decimal('1'), Decimal('1000'))
        order = exchange._validate_order(order)
        self.assertOrderEqual(order, correct_order)

        # limit sell more than resources[commodity]
        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.SELL, Decimal('2'), Decimal('1000'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.SELL, Decimal('1'), Decimal('1000'))
        order = exchange._validate_order(order)
        self.assertOrderEqual(order, correct_order)

        # limit buy more than resources[base]
        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.BUY, Decimal('11'), Decimal('10000'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.BUY, Decimal('10'), Decimal('10000'))
        order = exchange._validate_order(order)
        self.assertLessEqual(order._quantity, correct_order._quantity)
        order._quantity = Decimal('0')
        correct_order._quantity = Decimal('0')
        self.assertOrderEqual(order, correct_order)

        # more than max order size
        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.BUY, Decimal('100000'), Decimal('1'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.BUY, Decimal('10000'), Decimal('1'))
        order = exchange._validate_order(order)
        self.assertOrderEqual(order, correct_order)

        # first order size is decreased to resources, than becomes None
        exchange.resources['BTC'] = Decimal('0.00001')

        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.SELL, Decimal('1'), Decimal('1'))
        order = exchange._validate_order(order)
        self.assertIsNone(order)

        # order size decreased to resources[commodity] than quantized
        exchange.resources['BTC'] = Decimal('0.50000000001')

        order = Order('BTC_USD', OrderType.LIMIT,
                      OrderAction.SELL, Decimal('1'), Decimal('1'))
        correct_order = Order('BTC_USD', OrderType.LIMIT,
                              OrderAction.SELL, Decimal('0.5'), Decimal('1'))
        order = exchange._validate_order(order)
        self.assertOrderEqual(order, correct_order)

    def assertOrderEqual(self, o1, o2):
        self.assertEqual(o1.product, o2.product)
        self.assertEqual(o1._type, o2._type)
        self.assertEqual(o1._action, o2._action)
        self.assertEqual(o1._quantity, o2._quantity)

        if o1._price is None:
            self.assertIsNone(o2._price)

        elif o2._price is None:
            self.assertIsNone(o1._price)

        else:
            self.assertEqual(o1._price, o2._price)


class FakeExchange(CoinbasePro):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_resources(self):
        return self.resources

    def get_taker_fee(self, product):
        return Decimal('0.003')
