from rebalancer.utils import rebalance_orders,\
    get_weights_from_resources, topological_sort,\
    get_price_estimates_from_orderbooks, spread_to_fee, get_total_fee, \
    parse_market_orders
from typing import Dict
from exchange.exchange import Exchange
from decimal import Decimal


def market_order_rebalance(exchange: Exchange,
                           weights: Dict[str, Decimal],
                           base='USDT'):
    # TODO: rebalance with market orders
    resources = exchange.get_resources()
    currencies = (exchange.through_trade_currencies() |
                  set(list(resources.keys()) | list(weights.keys())))
    all_possible_products = ['_'.join([i, j])
                             for i in currencies
                             for j in currencies]

    orderbooks = exchange.get_orderbooks(all_possible_products)
    # getting all ordebrooks and filtering out orderbooks,
    # that use other currencies
    products = set(orderbook.product for orderbook in orderbooks)

    price_estimates = get_price_estimates_from_orderbooks(orderbooks, base)
    initial_weights = get_weights_from_resources(
        resources, price_estimates)

    orderbooks = {orderbook.product: orderbook
                  for orderbook in orderbooks}
    fees = {product: exchange.get_taker_fee(product)
            for product in products}

    spread_fees = {product: spread_to_fee(orderbook)
                   for product, orderbook in orderbooks.items()}

    total_fees = {product: get_total_fee(fees[product], spread_fees[product])
                  for product in products}

    orders = rebalance_orders(
        initial_weights, weights, total_fees)
    orders = topological_sort(orders)
    orders = [parse_market_orders(order, products, price_estimates, base)
              for order in orders]

    ret_orders = []
    for order in orders:
        ret_order = exchange.place_market_order(order, price_estimates)
        ret_orders.append(ret_order)

    return ret_orders
