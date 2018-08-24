import unittest
from exchange.binance import Binance
from internals.order import Order
from internals.enums import OrderType, OrderAction
from decimal import Decimal


class BinanceTester(unittest.TestCase):
    def test_validate_market_order(self):
        class FakeMarket(Binance):
            def __init__(self, filters, resources):
                self.resources = resources
                self.filters = filters

            def get_resources(self):
                return self.resources

        filters = {
            'BTCUSDT': {
                'min_order_size': Decimal('0.001'),
                'max_order_size': Decimal('10000'),
                'order_step': Decimal('1e-8'),
                'min_notional': Decimal('10'),
                'min_price': Decimal('1'),
                'max_price': Decimal('1e6'),
                'price_step': Decimal('0.01'),
                'base': 'USDT',
                'commodity': 'BTC'
            }
        }
        resources = {'BTC': Decimal('1e8'), 'USDT': Decimal('1e8')}

        fake_binance = FakeMarket(filters, resources)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal(1), None)
        price_estimates = {'BTC': Decimal('1e4'), 'USDT': Decimal(1)}
        new_order = fake_binance._validate_market_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertEqual(new_order._quantity, order._quantity)
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('0.0001'), None)
        new_order = fake_binance._validate_market_order(order, price_estimates)
        self.assertIsNone(new_order)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('1e6'), None)
        new_order = fake_binance._validate_market_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertEqual(new_order._quantity, Decimal('10000'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('1.000000001'), None)
        new_order = fake_binance._validate_market_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('0.001'), None)
        price_estimates = {'BTC': Decimal('100'), 'USDT': Decimal(1)}
        new_order = fake_binance._validate_market_order(order, price_estimates)
        self.assertIsNone(new_order)

        price_estimates = {'BTC': Decimal('10000'), 'USDT': Decimal(1)}
        fake_binance.resources = {
            'BTC': Decimal('1'),
            'USDT': Decimal('10000')
        }
        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('2'), None)
        new_order = fake_binance._validate_market_order(order, price_estimates)
        self.assertEqual(new_order.product, order.product)
        self.assertLessEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.BUY, Decimal('2'), None)
        new_order = fake_binance._validate_market_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertLessEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)
