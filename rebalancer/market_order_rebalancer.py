from rebalancer.utils import rebalance_orders,\
    get_weights_from_resources, topological_sort,\
    get_price_estimates_from_orderbooks
from typing import Dict
from exchange.exchange import Exchange
from decimal import Decimal


def market_order_rebalance(exchange: Exchange, weights: Dict[str, Decimal]):
    # TODO: rebalance with market orders
    orderbooks = exchange.get_orderbooks()
    initial_weights = get_weights_from_resources(
        exchange.get_resources(),
        get_price_estimates_from_orderbooks(orderbooks))
    orders = rebalance_orders(
        initial_weights, weights)
    orders = topological_sort(orders)
    ret_orders = []
    for order in orders:
        ret_order = exchange.place_market_order(order)
        ret_orders.append(ret_order)
    return ret_orders
