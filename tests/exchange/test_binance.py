import unittest
from exchange.binance import Binance
from internals.order import Order
from internals.enums import OrderType, OrderAction
from decimal import Decimal


class BinanceTester(unittest.TestCase):
    def test_validate_order(self):
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
        new_order = fake_binance._validate_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertEqual(new_order._quantity, order._quantity)
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('0.0001'), None)
        new_order = fake_binance._validate_order(order, price_estimates)
        self.assertIsNone(new_order)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('1e6'), None)
        new_order = fake_binance._validate_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertEqual(new_order._quantity, Decimal('10000'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('1.000000001'), None)
        new_order = fake_binance._validate_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('0.001'), None)
        price_estimates = {'BTC': Decimal('100'), 'USDT': Decimal(1)}
        new_order = fake_binance._validate_order(order, price_estimates)
        self.assertIsNone(new_order)

        price_estimates = {'BTC': Decimal('10000'), 'USDT': Decimal(1)}
        fake_binance.resources = {
            'BTC': Decimal('1'),
            'USDT': Decimal('10000')
        }
        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.SELL, Decimal('2'), None)
        new_order = fake_binance._validate_order(order, price_estimates)
        self.assertEqual(new_order.product, order.product)
        self.assertLessEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.MARKET,
                      OrderAction.BUY, Decimal('2'), None)
        new_order = fake_binance._validate_order(order, price_estimates)

        self.assertEqual(new_order.product, order.product)
        self.assertLessEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)

        order = Order('BTC_USDT', OrderType.LIMIT,
                      OrderAction.BUY, Decimal('2'), Decimal('0.01'))
        new_order = fake_binance._validate_order(order)
        self.assertIsNone(new_order)

        order = Order('BTC_USDT', OrderType.LIMIT,
                      OrderAction.BUY, Decimal('2'), Decimal('1e7'))
        new_order = fake_binance._validate_order(order)
        self.assertIsNone(new_order)

        order = Order('BTC_USDT', OrderType.LIMIT,
                      OrderAction.BUY, Decimal('2'), Decimal('150.0001'))
        new_order = fake_binance._validate_order(order)

        self.assertEqual(new_order.product, order.product)
        self.assertLessEqual(new_order._quantity, order._quantity)
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)
        self.assertEqual(new_order._price, Decimal('150'))

        order = Order('BTC_USDT', OrderType.LIMIT,
                      OrderAction.SELL, Decimal('2'), Decimal('150.0001'))
        new_order = fake_binance._validate_order(order)

        self.assertEqual(new_order.product, order.product)
        self.assertLessEqual(new_order._quantity, Decimal('1'))
        self.assertEqual(new_order._action, order._action)
        self.assertEqual(new_order._type, order._type)
        self.assertEqual(new_order._price, Decimal('150.01'))

    def test_parse_params(self):
        correct_params = {
            'symbol': 'BTCUSDT',
            'orderId': 10,
            'origClientOrderId': 'myOrder0'
        }
        product_symbol = {'product': 'BTC_USDT', 'symbol': 'BTCUSDT'}
        order_id = ['order_id', 'orderId']
        client_order_id = ['orig_client_order_id', 'origClientOrderId']
        params = [{
            'other_params': [1, 2, None, [4], {5: 6}],
            k: v,
            _id: 10,
            c_id: 'myOrder0'
        } for k, v in product_symbol.items()
            for _id in order_id
            for c_id in client_order_id]
        for param in params:
            self.assertDictEqual(Binance._parse_params(None, param),
                                 correct_params)

    def test_parse_market_order_response(self):
        resp = {
            "symbol": "BTCUSDT",
            "orderId": 28,
            "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
            "transactTime": 1507725176595,
            "price": "0.00000000",
            "origQty": "10.00000000",
            "executedQty": "10.00000000",
            "status": "FILLED",
            "timeInForce": "GTC",
            "type": "MARKET",
            "side": "SELL",
            "fills": [
                {
                    "price": "4000.00000000",
                    "qty": "1.00000000",
                    "commission": "4.00000000",
                    "commissionAsset": "BNB"
                },
                {
                    "price": "3999.00000000",
                    "qty": "5.00000000",
                    "commission": "19.99500000",
                    "commissionAsset": "BNB"
                },
                {
                    "price": "3998.00000000",
                    "qty": "2.00000000",
                    "commission": "7.99600000",
                    "commissionAsset": "USDT"
                },
                {
                    "price": "3997.00000000",
                    "qty": "1.00000000",
                    "commission": "3.99700000",
                    "commissionAsset": "USDT"
                },
                {
                    "price": "3995.00000000",
                    "qty": "1.00000000",
                    "commission": "3.99500000",
                    "commissionAsset": "USDT"
                }
            ]
        }
        ret = Binance.parse_market_order_response(None, resp)
        correct_parsed_response = {
            "orderId": 28,
            "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
            "executed_quantity": Decimal("10.00000000"),
            "mean_price": Decimal("3998.30000000"),
            "commission_USDT": Decimal("15.98800000"),
            "commission_BNB": Decimal("23.99500000"),
            "symbol": "BTCUSDT"
        }

        self.assertDictEqual(correct_parsed_response, ret)
