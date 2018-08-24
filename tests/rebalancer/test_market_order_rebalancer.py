import unittest
from decimal import Decimal

from internals.orderbook import OrderBook
from exchange.binance import Binance
from internals.enums import OrderType, OrderAction

from rebalancer.market_order_rebalancer import market_order_rebalance


class MarketOrderRebalancerTester(unittest.TestCase):
    def test_market_order_rebalance(self):
        # using tests from test_utils: UtilsTester.test_rebalance_orders
        initial_weights = {'BTC': Decimal('0.2'),
                           'ETH': Decimal('0.3'),
                           'USDT': Decimal('0.5')}
        final_weights = {'BTC': Decimal('0.5'),
                         'ETH': Decimal('0.2'),
                         'USDT': Decimal('0.3')}

        resources = {'BTC': Decimal('1') * initial_weights['BTC'],
                     'USDT': Decimal('10000') * initial_weights['USDT'],
                     'ETH': Decimal('10') * initial_weights['ETH']}
        currencies = {'BTC', 'USDT', 'ETH'}
        fees = {'BTC_USDT': Decimal('0.001'),
                'ETH_USDT': Decimal('0.001'),
                'ETH_BTC': Decimal('0.001')}

        filters = {'BTCUSDT': {
            'min_order_size': Decimal('1e-3'),
            'max_order_size': Decimal('1e6'),
            'order_step': Decimal('1e-8'),
            'min_notional': Decimal('1'),
            'base': 'USDT',
            'commodity': 'BTC'
        },
            'ETHUSDT': {
                'min_order_size': Decimal('1e-5'),
                'max_order_size': Decimal('1e4'),
                'order_step': Decimal('1e-8'),
                'min_notional': Decimal('1'),
                'base': 'USDT',
                'commodity': 'ETH'
        },
            'ETHBTC': {
                'min_order_size': Decimal('1e-2'),
                'max_order_size': Decimal('1e5'),
                'order_step': Decimal('1e-8'),
                'min_notional': Decimal('1e-5'),
                'base': 'BTC',
                'commodity': 'ETH'
        }
        }

        spread_BTC_USDT = Decimal('1')
        orderbook_BTC_USDT = OrderBook(
            'BTC_USDT',
            [Decimal('10000') * spread_BTC_USDT,
             Decimal('10000') / spread_BTC_USDT])
        spread_ETH_USDT = Decimal('1')
        orderbook_ETH_USDT = OrderBook(
            'ETH_USDT',
            [Decimal('1000') * spread_ETH_USDT,
             Decimal('1000') / spread_ETH_USDT])
        spread_ETH_BTC = Decimal('1')
        orderbook_ETH_BTC = OrderBook(
            'ETH_BTC',
            [Decimal('0.1') * spread_ETH_BTC,
             Decimal('0.1') / spread_ETH_BTC])

        orderbooks = [orderbook_ETH_BTC,
                      orderbook_ETH_USDT,
                      orderbook_BTC_USDT]

        base = 'USDT'

        exchange = FakeExchange(resources=resources,
                                orderbooks=orderbooks,
                                _through_trade_currencies=currencies,
                                fees=fees,
                                filters=filters)

        market_order_rebalance(exchange, final_weights, base)

        orders = exchange.orders
        for order in orders:
            self.assertEqual(order._type, OrderType.MARKET)

        parsed_orders = [parse_order(order) for order in orders]
        parsed_orders.sort()

        self.assertEqual(parsed_orders[0][:2], ('ETH', 'BTC'))
        self.assertEqual(parsed_orders[0][2], Decimal('1'))
        self.assertEqual(parsed_orders[1][:2], ('USDT', 'BTC'))
        self.assertEqual(parsed_orders[1][2], Decimal('0.2'))

        fees2 = {'BTC_USDT': Decimal('0.002'),
                 'ETH_USDT': Decimal('0.0008'),
                 'ETH_BTC': Decimal('0.0009')}

        exchange = FakeExchange(resources=resources,
                                orderbooks=orderbooks,
                                _through_trade_currencies=currencies,
                                fees=fees2,
                                filters=filters)

        market_order_rebalance(exchange, final_weights, base)

        orders = exchange.orders
        for order in orders:
            self.assertEqual(order._type, OrderType.MARKET)

        parsed_orders = [parse_order(order) for order in orders]
        parsed_orders.sort()
        self.assertEqual(parsed_orders[0][:2], ('ETH', 'BTC'))
        self.assertEqual(parsed_orders[0][2], Decimal('3'))
        self.assertEqual(parsed_orders[1][:2], ('USDT', 'ETH'))
        self.assertEqual(parsed_orders[1][2], Decimal('2'))

        fees2 = {'BTC_USDT': Decimal('0.001'),
                 'ETH_USDT': Decimal('0.001'),
                 'ETH_BTC': Decimal('0.001')}

        spread_BTC_USDT = Decimal('0.996996997')
        orderbook_BTC_USDT = OrderBook(
            'BTC_USDT',
            [Decimal('10000') * spread_BTC_USDT,
             Decimal('10000') / spread_BTC_USDT])
        spread_ETH_USDT = Decimal('0.999499499')
        orderbook_ETH_USDT = OrderBook(
            'ETH_USDT',
            [Decimal('1000') * spread_ETH_USDT,
             Decimal('1000') / spread_ETH_USDT])
        spread_ETH_BTC = Decimal('0.999499499')
        orderbook_ETH_BTC = OrderBook(
            'ETH_BTC',
            [Decimal('0.1') * spread_ETH_BTC,
             Decimal('0.1') / spread_ETH_BTC])

        orderbooks = [orderbook_ETH_BTC,
                      orderbook_ETH_USDT,
                      orderbook_BTC_USDT]

        exchange = FakeExchange(resources=resources,
                                orderbooks=orderbooks,
                                _through_trade_currencies=currencies,
                                fees=fees2,
                                filters=filters)

        market_order_rebalance(exchange, final_weights, base)

        orders = exchange.orders
        for order in orders:
            self.assertEqual(order._type, OrderType.MARKET)

        parsed_orders = [parse_order(order) for order in orders]
        parsed_orders.sort()
        self.assertEqual(parsed_orders[0][:2], ('ETH', 'BTC'))
        self.assertAlmostEqual(parsed_orders[0][2], Decimal('3'), places=5)
        self.assertEqual(parsed_orders[1][:2], ('USDT', 'ETH'))
        self.assertAlmostEqual(parsed_orders[1][2], Decimal('2'), places=5)


def parse_order(order):
    product = order.product
    currency_pair = product.split('_')
    if order._action == OrderAction.BUY:
        currency_pair = currency_pair[::-1]
    quantity = order._quantity
    return (*currency_pair, quantity)


class FakeExchange(Binance):
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.orders = []

    def get_resources(self):
        return self.resources

    def through_trade_currencies(self):
        return self._through_trade_currencies

    def get_orderbooks(self, products):
        return self.orderbooks

    def get_taker_fee(self, product):
        return self.fees[product]

    def place_market_order(self, order, price_estimates):
        order = self._validate_market_order(order, price_estimates)
        if order is None:
            return
        self.orders.append(order)
