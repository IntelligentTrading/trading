from decimal import Decimal
from typing import Dict
import time

from internals.enums import OrderType, OrderAction
from exchange.exchange import Exchange
from rebalancer.utils import rebalance_orders, get_total_fee, \
    parse_order, pre_rebalance


def limit_order_rebalance(exchange: Exchange,
                          weights: Dict[str, Decimal],
                          retries: int = 10,
                          time_delta: int = 30,
                          base: str='USDT'):
    (products, orderbooks, price_estimates, portfolio_value, initial_weights,
     fees, spread_fees) = pre_rebalance(exchange, weights, base)
    reverse_spread_fees = {product: 1 - 1 / (1 - spread_fee)
                           for product, spread_fee in spread_fees.items()}

    limit_pseudo_fee = Decimal('1e2')
    # adding 2 to each cost
    # because total cost is less than 2, algorithm will minimize number of
    # orders first, than total fee
    total_fees = {product: (1 - get_total_fee(
        fees[product], reverse_spread_fees[product])) / limit_pseudo_fee
        for product in products}

    orders = rebalance_orders(
        initial_weights, weights, total_fees)

    orders = [(*order[:2], order[2] * portfolio_value) for order in orders]
    orders = [parse_order(order, products,
                          price_estimates, base,
                          OrderType.LIMIT, Decimal())
              for order in orders]

    number_of_trials = {}
    rets = []
    while len(number_of_trials) == 0 or all(
            v <= retries for v in number_of_trials.values()):
        orderbooks = exchange.get_orderbooks(products)
        currencies_from = set()
        currencies_to = set()
        for order in orders:
            currency_commodity, currency_base = order.product.split('_')
            if order._action == OrderAction.SELL:
                currencies_from.add(currency_commodity)
                currencies_to.add(currency_base)
            else:
                currencies_to.add(currency_commodity)
                currencies_from.add(currency_base)

        currencies_free = currencies_from - currencies_to

        order_responses = []
        orders_to_remove = []
        for order in orders:
            currency_commodity, currency_base = order.product.split('_')
            orderbook = orderbooks[order.product]
            # TODO: check resources
            if (order._action == OrderAction.SELL and
                    currency_commodity not in currencies_free):
                # if selling commodity, which we don't have yet
                continue
            elif (order._action == OrderAction.BUY and
                    currency_base not in currencies_free):
                # if buying commodity, for which we don't have base yet
                continue
            order._price = orderbook.get_mid_market_price()
            order_response = exchange.place_limit_order(order)
            if order_response is not None:
                order_response.update({'order': order})
                order_responses.append(order_response)
            else:
                if not isinstance(order_response, Exception):
                    orders_to_remove.append(order)

        for order in orders_to_remove:
            orders.remove(order)
        time.sleep(time_delta)

        for order_response in order_responses:
            exchange.cancel_limit_order(order_response)
            resp = exchange.get_order(order_response)
            rets.append(resp)
            order = order_response['order']
            if (Decimal(resp['orig_quantity']) -
                    Decimal(resp['executed_quantity'])) > Decimal('1e-3'):
                order._quantity = Decimal(
                    resp['orig_quantity']) - Decimal(resp['executed_quantity'])

                if order.product not in number_of_trials:
                    number_of_trials[order.product] = 0
                number_of_trials[order.product] += 1

            else:
                orders.remove(order)

    return rets
