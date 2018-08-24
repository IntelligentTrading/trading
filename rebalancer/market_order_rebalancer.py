from rebalancer.utils import rebalance_orders,\
    get_weights_from_resources, topological_sort,\
    get_price_estimates_from_orderbooks, parse_market_orders
from typing import Dict
from exchange.exchange import Exchange
from decimal import Decimal


def market_order_rebalance(exchange: Exchange,
                           weights: Dict[str, Decimal],
                           base='USDT'):
    # TODO: rebalance with market orders
    orderbooks = exchange.get_orderbooks()
    products = set(orderbook.product for orderbook in orderbooks)

    price_estimates = get_price_estimates_from_orderbooks(orderbooks, base)
    initial_weights = get_weights_from_resources(
        exchange.get_resources(), price_estimates)

    orders = rebalance_orders(
        initial_weights, weights)
    orders = topological_sort(orders)
    orders = [parse_market_orders(order, products, price_estimates, base)
              for order in orders]

    ret_orders = []
    for order in orders:
        ret_order = exchange.place_market_order(order, price_estimates)
        ret_orders.append(ret_order)

    return ret_orders
