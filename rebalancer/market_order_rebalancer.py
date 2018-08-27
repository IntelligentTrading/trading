from rebalancer.utils import rebalance_orders, topological_sort, \
    get_total_fee, parse_order, pre_rebalance
from typing import Dict
from exchange.exchange import Exchange
from decimal import Decimal


def market_order_rebalance(exchange: Exchange,
                           weights: Dict[str, Decimal],
                           base: str='USDT'):
    (products, orderbooks, price_estimates, portfolio_value, initial_weights,
     fees, spread_fees) = pre_rebalance(exchange, weights, base)
    total_fees = {product: 1 - get_total_fee(fees[product],
                                             spread_fees[product])
                  for product in products}

    orders = rebalance_orders(
        initial_weights, weights, total_fees)
    orders = [(*order[:2], order[2] * portfolio_value) for order in orders]
    orders = topological_sort(orders)
    orders = [parse_order(order, products,
                          price_estimates,
                          base)
              for order in orders]

    ret_orders = []
    for order in orders:
        for i in range(10):
            ret_order = exchange.place_market_order(order, price_estimates)
            if not isinstance(ret_order, Exception):
                break

        ret_orders.append(ret_order)

    return ret_orders
