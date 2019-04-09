from decimal import Decimal
from typing import List, Dict
from cbpro import PublicClient, AuthenticatedClient

from logger import logger
from exchange.exchange import Exchange
from internals.order import Order
from internals.orderbook import OrderBook
from internals.utils import quantize


class CoinbasePro(Exchange):
    def __init__(self, api_key: str=None,
                 secret_key: str=None,
                 passphrase: str=None):
        super().__init__()
        if any(i is None for i in [api_key, secret_key, passphrase]):
            self.client = PublicClient()
        else:
            self.client = AuthenticatedClient(api_key, secret_key, passphrase)

        self.products = self.client.get_products()
        self.filters = {product['id']: {
            'min_order_size': Decimal(product['base_min_size']),
            'max_order_size': Decimal(product['base_max_size']),
            'order_step': Decimal('1e-8'),
            'price_step': Decimal(product['quote_increment']),
            'base': product['quote_currency'],
            'commodity': product['base_currency']
        } for product in self.products}

    def through_trade_currencies(self):
        return {'BTC', 'USD'}

    def get_taker_fee(self, product):
        return Decimal('0.003')

    def get_maker_fee(self, product):
        return Decimal('0')

    def get_resources(self):
        return {account['currency']: Decimal(account['available'])
                for account in self.client.get_accounts()}

    def place_market_order(self, order: Order,
                           price_estimates: Dict[str, Decimal]):

        logger.info("creating market order - {}".format(str(order)))
        order = self.validate_order(order, price_estimates)
        symbol = order.product.replace('_', '-')
        logger.info("validated order - {}".format(str(order)))
        resp = self.client.place_market_order(
            symbol, order._action.name.lower(), size=order._quantity)

        parsed_response = self.parse_market_order_response(resp)
        parsed_response['price_estimates'] = price_estimates
        parsed_response['product'] = parsed_response['symbol'].replace(
            '-', '_')
        logger.info("parsed order response - {}".format(str(parsed_response)))
        return parsed_response

    def place_limit_order(self, order: Order):
        logger.info("creating limit order - {}".format(str(order)))
        order = self.validate_order(order)
        logger.info("validated order - {}".format(str(order)))
        symbol = order.product.replace('_', '-')
        resp = self.client.place_market_order(symbol,
                                              order._action.name.lower(),
                                              order._price, order._quantity,
                                              post_only=True)
        logger.info("order response - {}".format(str(resp)))
        return {'order_id': resp['id']}

    def _validate_order(self, order, price_estimates=None):
        resources = self.get_resources()
        symbol = order.product.replace('_', '-')
        filt = self.filters[symbol]
        base, commodity = filt['base'], filt['commodity']
        # quantity
        if order._quantity < filt['min_order_size']:
            return

        if order._quantity > filt['max_order_size']:
            order._quantity = filt['max_order_size']

        if order._quantity % filt['order_step'] > 0:
            order._quantity = quantize(order._quantity, filt['order_step'])

        # price
        if order._price is not None:
            if order._price % filt['price_step'] > 0:
                order._price = quantize(order._price, filt['price_step'],
                                        down=(order._action.name == 'BUY'))

        # resources
        if order._action.name == 'SELL':
            if order._quantity > resources[commodity]:
                order._quantity = resources[commodity]
                order = self._validate_order(order, price_estimates)
        else:
            epsilon = Decimal('1.0001')
            if order._price is not None:
                price = order._price
                if price * order._quantity > resources[base]:
                    order._quantity = resources[base] / (
                        price * epsilon)
                    order = self._validate_order(order, price_estimates)
            else:
                price = price_estimates[commodity] / price_estimates[base]
                fee = self.get_taker_fee(order.product) + 1
                if price * order._quantity * fee > resources[base]:
                    order._quantity = resources[base] / (price * fee * epsilon)
                    order = self._validate_order(order, price_estimates)
        return order

    def parse_market_order_response(self, response):
        fills = self.client.get_fills(response['id'])
        total_size = [Decimal(fill['size']) for fill in fills]
        total_money = [Decimal(fill['size']) * Decimal(fill['price'])
                       for fill in fills]
        fee_asset = response['product_id'].split('-')[-1]
        product = response['product_id'].replace('-', '_')
        fee = self.get_taker_fee(product) * total_money
        return {'symbol': response['product_id'],
                'orderId': response['id'],
                'executed_quantity': Decimal(response['executed_value']),
                'mean_price': total_money / total_size,
                'commission_' + fee_asset: fee,
                'side': response['side']}

    def cancel_limit_order(self, response):
        logger.info("canceled order - {}".format(response))
        order_id = response['order_id']
        return self.client.cancel_order(order_id)

    def get_order(self, response):
        logger.info("get order = {}".format(str(response)))
        order_id = response['order_id']
        resp = self.client.get_order(order_id)
        # TODO: executed quantity and orig_quantity
        resp.update({'executed_quantity': Decimal(resp['executed_value']),
                     'orig_quantity': Decimal(resp['size'])})
        logger.info("get order response - {}".format(str(resp)))
        return resp

    def get_orderbooks(self, products: List[str]=None, depth: int=1):
        if products is None:
            products = [product['id'].replace('-', '_') for product in self.products]
        orderbooks = []
        for product in products:
            symbol = product.replace('_', '-')
            raw_orderbook = self.client.get_product_order_book(symbol)
            if len(raw_orderbook['bids']) == 0 or len(raw_orderbook['asks']) == 0:
                continue
            orderbook = OrderBook(product,
                                  {'bid': Decimal(raw_orderbook['bids'][0][0]),
                                   'ask': Decimal(raw_orderbook['asks'][0][0])})
            orderbooks.append(orderbook)
        return orderbooks
