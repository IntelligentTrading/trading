from decimal import Decimal
from binance.client import Client
from binance.exceptions import BinanceAPIException

from logger import logger
from exchange.exchange import Exchange
from internals.utils import binance_product_to_currencies
from internals.utils import quantize
from internals.orderbook import OrderBook


class Binance(Exchange):
    def __init__(self, api_key: str=None, secret_key: str=None):
        super().__init__()
        self.client = Client(api_key, secret_key)
        filters = self.client.get_exchange_info()['symbols']
        self.filters = {
            filt['symbol']: {
                'min_order_size': Decimal(filt['filters'][1]['minQty']),
                'max_order_size': Decimal(filt['filters'][1]['maxQty']),
                'order_step': Decimal(filt['filters'][1]['stepSize']),
                'min_notional': Decimal(filt['filters'][2]['minNotional']),
                'min_price': Decimal(filt['filters'][0]['minPrice']),
                'max_price': Decimal(filt['filters'][0]['maxPrice']),
                'price_step': Decimal(filt['filters'][0]['tickSize']),
                'base': filt['quoteAsset'],
                'commodity': filt['baseAsset'],
            }
            for filt in filters if 'minQty' in filt['filters'][1]
        }

    def get_mid_price_orderbooks(self, products=None):
        prices_list = self.client.get_all_tickers()
        orderbooks = []
        for price_symbol in prices_list:
            currency_pair = binance_product_to_currencies(
                price_symbol['symbol'])
            product = '_'.join(currency_pair)
            if products is not None and product not in products:
                continue
            orderbook = OrderBook(
                product, Decimal(price_symbol['price']))
            if orderbook.get_wall_ask() <= Decimal('1e-8'):
                continue
            orderbooks.append(orderbook)
        return orderbooks

    def get_orderbooks(self, products=None, depth: int=1):
        if depth != 1:
            raise NotImplementedError
        if products is not None:
            products = set(products)
        return self.get_orderbooks_of_depth1(products)

    def get_orderbooks_of_depth1(self, products):
        """
        get all orderbooks with depth equal to 1, then filter out those,
        which symbol is not in specified products
        """
        books_list = self.client.get_orderbook_tickers()
        orderbooks = []
        for book in books_list:
            currency_pair = binance_product_to_currencies(
                book['symbol'])
            if not currency_pair:
                continue
            product = '_'.join(currency_pair)
            if products is not None and product not in products:
                continue
            orderbook = OrderBook(
                product, {'ask': Decimal(book['askPrice']),
                          'bid': Decimal(book['bidPrice'])})
            if orderbook.get_wall_ask() <= Decimal('1e-8'):
                continue
            orderbooks.append(orderbook)
        return orderbooks

    def get_taker_fee(self, product):
        return Decimal('0.001')

    def get_maker_fee(self, product):
        return Decimal('0.001')

    def through_trade_currencies(self):
        return {'BTC', 'BNB', 'ETH', 'USDT'}

    def get_resources(self):
        return {asset_balance['asset']: Decimal(asset_balance['free'])
                for asset_balance in self.client.get_account()['balances']
                if Decimal(asset_balance['free']) > Decimal(0)}

    def place_limit_order(self, order):
        logger.info("creating limit order - {}".format(str(order)))
        order = self._validate_order(order)
        logger.info("validated order - {}".format(str(order)))
        if order is None:
            return
        symbol = ''.join(order.product.split('_'))
        side = order._action.name
        quantity = order._quantity
        new_order_resp_type = 'FULL'
        price = order._price
        try:
            resp = self.client.create_order(
                side=side, symbol=symbol,
                quantity=quantity,
                newOrderRespType=new_order_resp_type,
                price=price.to_eng_string(),
                type=self.client.ORDER_TYPE_LIMIT_MAKER)
        except BinanceAPIException as e:
            return e

        order_id = resp['orderId']
        client_order_id = resp['clientOrderId']
        logger.info("order response - {}".format(str(resp)))

        return {'symbol': resp['symbol'],
                'orderId': order_id,
                'clientOrderId': client_order_id}

    def place_market_order(self, order, price_estimates):
        """
        place market order
        uses price estimates to check min notional and resources for buy orders
        returns dict with keys
        {'orderId', 'clientOrderId', 'executed_quantity', 'mean_price'}
        with corresponding values

        also returns commission_asset: fee
        for example
        {
            "orderId": 28,
            "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
            "executed_quantity": Decimal("10.00000000"),
            "mean_price": Decimal("3998.30000000"),
            "commission_USDT": Decimal("19.99150000"),
            "commission_BNB": Decimal("11.66365227")
        }
        """
        logger.info("creating market order - {}".format(str(order)))
        order = self._validate_order(order, price_estimates)
        logger.info("validated order - {}".format(str(order)))
        if order is None:
            return
        symbol = ''.join(order.product.split('_'))
        side = order._action.name
        quantity = order._quantity
        newOrderRespType = 'FULL'
        try:
            resp = self.client.order_market(side=side, symbol=symbol,
                                            quantity=quantity,
                                            newOrderRespType=newOrderRespType)
        except BinanceAPIException as e:
            return e

        parsed_response = self.parse_market_order_response(resp)
        parsed_response['price_estimates'] = price_estimates
        parsed_response['product'] = '_'.join(binance_product_to_currencies(
            parsed_response['symbol']))
        logger.info("parsed order response - {}".format(str(parsed_response)))
        return parsed_response

    def parse_market_order_response(self, resp):
        order_id = resp['orderId']
        client_order_id = resp['clientOrderId']
        executed_quantity = Decimal(resp['executedQty'])
        fills = resp['fills']
        value = sum(Decimal(fill['qty']) * Decimal(fill['price'])
                    for fill in fills)
        total_quantity = sum(Decimal(fill['qty']) for fill in fills)
        mean_price = value / total_quantity
        commissions = {}
        for fill in fills:
            if fill['commissionAsset'] not in commissions:
                commissions[fill['commissionAsset']] = Decimal()
            commissions[fill['commissionAsset']] += Decimal(fill['commission'])

        ret = {
            'symbol': resp['symbol'],
            'orderId': order_id,
            'clientOrderId': client_order_id,
            'executed_quantity': executed_quantity,
            'mean_price': mean_price,
            'side': resp['side']}

        for asset, fee in commissions.items():
            ret['commission_' + asset] = fee

        return ret

    def _validate_order(self, order, price_estimates=None):
        resources = self.get_resources()
        symbol = ''.join(order.product.split('_'))
        filt = self.filters[symbol]

        if order._quantity < filt['min_order_size']:
            return
        if order._quantity > filt['max_order_size']:
            order._quantity = filt['max_order_size']
        order._quantity = quantize(order._quantity, filt['order_step'])

        if order._price is not None:
            if order._price < filt['min_price']:
                return
            if order._price > filt['max_price']:
                return
            if order._price % filt['price_step'] != 0:
                order._price = quantize(order._price, filt['price_step'],
                                        down=order._action.name == 'BUY')

        if order._price is None:
            value = (price_estimates[filt['commodity']] /
                     price_estimates[filt['base']]) * order._quantity
        else:
            value = order._price * order._quantity
        if value < filt['min_notional']:
            return

        if order._action.name == 'SELL':
            if resources[filt['commodity']] < order._quantity:
                order._quantity = resources[filt['commodity']]
                order = self._validate_order(order, price_estimates)
        else:
            if order._price is None:
                price_commodity = price_estimates[filt['commodity']]
                price_base = price_estimates[filt['base']]
                price = price_commodity / price_base
            else:
                price = order._price
            if resources[filt['base']] < order._quantity * price:
                order._quantity = resources[filt['base']] / (
                    price * Decimal('1.0001'))
                # any number
                order = self._validate_order(order, price_estimates)
        return order

    def get_order(self, params):
        """
        symbol or product: str
        order_id or orderId: int
        client_order_id  or origClientOrderId: str, optional
        :return: similiar to example
            {
                "symbol": "LTCBTC",
                "orderId": 1,
                "clientOrderId": "myOrder1",
                "price": "0.1",
                "origQty": "1.0",
                "orig_quantity": "1.0",
                "executedQty": "0.0",
                "executed_quantity": "0.0",
                "status": "NEW",
                "timeInForce": "GTC",
                "type": "LIMIT",
                "side": "BUY",
                "stopPrice": "0.0",
                "icebergQty": "0.0",
                "time": 1499827319559
            }
        """
        logger.info("get order = {}".format(str(params)))
        d = self._parse_params(params)
        resp = self.client.get_order(**d)
        resp.update({'orig_quantity': resp['origQty'],
                     'executed_quantity': resp['executedQty']})
        logger.info("get order response - {}".format(str(resp)))
        return resp

    def cancel_limit_order(self, params):
        """
        symbol or product: str
        order_id or orderId: int
        client_order_id  or origClientOrderId: str, optional
        :return: similiar to example
            {
                "symbol": "LTCBTC",
                "origClientOrderId": "myOrder1",
                "orderId": 1,
                "clientOrderId": "cancelMyOrder1"
            }
        """
        logger.info("canceled order - {}".format(str(params)))
        d = self._parse_params(params)
        try:
            resp = self.client.cancel_order(**d)
        except BinanceAPIException as e:
            if e.message != "UNKNOWN_ORDER":
                raise e
            logger.warning("Exception{code} with message ={message}".format(
                code=e.code, message=e.message))
            resp = {}
        return resp

    def _parse_params(self, params):
        d = {}
        assert 'product' in params or 'symbol' in params
        if 'product' in params:
            d['symbol'] = ''.join(params['product'].split('_'))
        else:
            d['symbol'] = params['symbol']

        if 'order_id' in params or 'orderId' in params:
            d['orderId'] = params.get('order_id') or params['orderId']
        if 'origClientOrderId' in params or 'orig_client_order_id' in params:
            d['origClientOrderId'] = params.get(
                'orig_client_order_id') or params['origClientOrderId']
        assert d.get('origClientOrderId') is not None or d.get(
            'orderId') is not None
        return d
