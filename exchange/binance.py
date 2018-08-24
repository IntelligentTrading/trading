from exchange.exchange import Exchange
from internals.orderbook import OrderBook
from internals.utils import binance_product_to_currencies
from decimal import Decimal
from binance.client import Client
from binance.exceptions import BinanceAPIException


class Binance(Exchange):
    def __init__(self, api_key: str=None, secret_key: str=None):
        super().__init__()
        self.client = Client(api_key, secret_key)
        filters = self.client.get_exchange_info()['symbols']
        self.filters = {
            filt['symbol']: {
                'min_order_size': filt['filters'][1]['minQty'],
                'max_order_size': filt['filters'][1]['maxQty'],
                'order_step': filt['filters'][1]['stepSize'],
                'min_notional': filt['filters'][2]['minNotional'],
                'min_price': filt['filters'][0]['minPrice'],
                'max_price': filt['filters'][0]['maxPrice'],
                'price_step': filt['filters'][0]['tickSize'],
                'base': filt['baseAsset'],
                'commodity': filt['quoteAsset'],
            }
            for filt in filters
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
            product = '_'.join(currency_pair)
            if products is not None and product not in products:
                continue
            orderbook = OrderBook(
                product, {'ask': Decimal(book['askPrice']),
                          'bid': Decimal(book['bidPrice'])})
            orderbooks.append(orderbook)
        return orderbooks

    def get_taker_fee(self, product):
        return Decimal('0.001')

    def through_trade_currencies(self):
        return {'BTC', 'BNB', 'ETH', 'USDT'}

    def get_resources(self):
        return {asset_balance['asset']: Decimal(asset_balance['free'])
                for asset_balance in self.client.get_account()['balances']}

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
        order = self._validate_market_order(order, price_estimates)
        if order is None:
            return
        symbol = ''.join(order.product.split('_'))
        side = order.side.name
        quantity = order.quantity
        newOrderRespType = 'FULL'
        try:
            resp = self.client.order_market(side=side, symbol=symbol,
                                            quantity=quantity,
                                            newOrderRespType=newOrderRespType)
        except BinanceAPIException as e:
            return

        orderId = resp['orderId']
        clientOrderId = resp['clientOrderId']
        executed_quantity = Decimal(resp['executed_quantity'])
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
            'orderId': orderId,
            'clientOrderId': clientOrderId,
            'executed_quantity': executed_quantity,
            'mean_price': mean_price}

        for asset, fee in commissions.items():
            ret['commission_' + asset] = fee

        return ret

    def _validate_market_order(self, order, price_estimates):
        resources = self.get_resources()
        symbol = ''.join(order.product.split('_'))
        filt = self.filters[symbol]

        if order._quantity < filt['min_order_size']:
            return
        if order._quantity > filt['max_order_size']:
            order._quantity = filt['max_order_size']
        order._quantity = order._quantity // filt['order_step'] * (
            filt['order_step'])

        value = (price_estimates[filt['commodity']] /
                 price_estimates[filt['base']]) * order._quantity
        if value < filt['min_notional']:
            return

        if order._action.name == 'SELL':
            if resources[filt['commodity']] < order._quantity:
                order._quantity = resources[filt['commodity']]
                order = self._validate_market_order(order, price_estimates)
        else:
            price_commodity = price_estimates[filt['commodity']]
            price_base = price_estimates[filt['base']]
            price = price_commodity / price_base
            if resources[filt['base']] < order._quantity * price:
                order._quantity = resources[filt['base']] / (
                    price * Decimal('1.0001'))
                # any number
                order = self._validate_market_order(order, price_estimates)
        return order
