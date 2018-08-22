from rebalancer.utils import rebalance_orders,\
    get_weights_from_resources, topological_sort,\
    get_prices_from_orderbook
from typing import Dict
from exchange.exchange import Exchange
from decimal import Decimal


def market_order_rebalance(exchange: Exchange, weights: Dict[str, Decimal]):
    # TODO: rebalance with market orders
    initial_weights = get_weights_from_resources(exchange.get_resources())
    orderbook = exchange.get_order_book()
    orders = rebalance_orders(
        initial_weights, weights, get_prices_from_orderbook(orderbook))
    orders = topological_sort(orders)
    ret_orders = []
    for order in orders:
        ret_order = exchange.place_market_order(order)
        ret_orders.append(ret_order)
    return ret_orders
