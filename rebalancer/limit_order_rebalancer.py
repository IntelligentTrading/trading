from decimal import Decimal
from typing import Dict, List
import time
from internals.order import Order
from internals.enums import OrderType, OrderAction
from exchange.exchange import Exchange
from rebalancer.utils import rebalance_orders, get_total_fee, \
    parse_order, pre_rebalance


def limit_order_rebalance_retry_after_time_estimate(number_of_trials,
                                                    max_retries, time_delta):
    mean_retries = sum(max_retries - v for v in number_of_trials.values()
                       ) / len(number_of_trials)
    needed_time = int(mean_retries * time_delta * 3) * 1000
    return needed_time


def limit_order_rebalance(exchange: Exchange,
                          weights: Dict[str, Decimal],
                          user, update_function, *,
                          max_retries: int = 10,
                          time_delta: int = 30,
                          base: str='USDT'):
    (products, resources, orderbooks, price_estimates,
     portfolio_value, initial_weights,
     spread_fees) = pre_rebalance(exchange, weights, base)

    fees = {product: exchange.get_maker_fee(product)
            for product in products}

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
    return limit_order_rebalance_with_orders(update_function, exchange,
                                             resources, products,
                                             orders, max_retries,
                                             time_delta, base)


def limit_order_rebalance_with_orders(update_function,
                                      exchange: Exchange,
                                      resources: Dict[str, Decimal],
                                      products: List[str],
                                      orders: List[Order],
                                      max_retries: int,
                                      time_delta: int,
                                      base: str):
    number_of_trials = {order.product: 0 for order in orders}
    rets = []
    while len(orders) and (all(
        number_of_trials[order.product] <= max_retries
            for order in orders)):
        orderbooks = exchange.get_orderbooks(products)
        orderbooks = {ob.product: ob for ob in orderbooks}
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
            order._price = orderbook.get_mid_market_price()
            if order._action == OrderAction.SELL:
                if (currency_commodity not in currencies_free and
                        resources[currency_commodity] < order._quantity):
                    # if selling commodity, which we don't have yet
                    continue
            else:
                if (currency_base not in currencies_free and
                        resources[currency_base] <
                        order._quantity * order._price):
                    # if buying commodity, for which we don't have base yet
                    continue
            order_response = exchange.place_limit_order(order)
            if order_response is None:
                number_of_trials[order.product] = max_retries
                orders_to_remove.append(order)
            elif not isinstance(order_response, Exception):
                order_response.update({'order': order})
                order_responses.append(order_response)
            else:
                number_of_trials[order.product] += 1
        for order in orders_to_remove:
            number_of_trials[order.product] = max_retries
            orders.remove(order)

        update_function(limit_order_rebalance_retry_after_time_estimate(
            number_of_trials, max_retries, time_delta))
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

                number_of_trials[order.product] += 1
            else:
                number_of_trials[order.product] = max_retries
                orders.remove(order)

    return rets
