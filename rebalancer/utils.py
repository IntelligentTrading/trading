from internals.orderbook import OrderBook
from typing import List, Dict, Tuple
from decimal import Decimal
from collections import defaultdict


def rebalance_orders(initial_weights: Dict[str, Decimal],
                     final_weights: Dict[str, Decimal],
                     prices: Dict[str, Decimal]) -> (
        List[Tuple[str, str, Decimal]]):
    """
    :param initial_weights: weights before rebalance
    :param final_weights: weights after rebalance
    :param prices: product to price dict
                (maybe we will use also {'BTC_USDT': 1000, 'USDT_BTC':0.001})
    :return: List of orders, each order is list of length 3,
                             currency from, currency to, quantity
                                                (might be product, quantity)
    """
    raise NotImplementedError


def get_weights_from_resources(
        resources: Dict[str, Decimal],
        prices: Dict[str, Decimal]) -> Dict[str, Decimal]:
    resources_in_base = {
        currency: resources[currency] * prices[currency]
        for currency in resources
    }
    portfolio_value = sum(resources_in_base.values())
    weights = {
        currency: resources_in_base[currency] / portfolio_value
        for currency in resources_in_base
    }
    return weights


def get_mid_prices_from_orderbooks(orderbooks: List[OrderBook]) -> (
        Dict[str, Decimal]):
    prices = {orderbook.product: orderbook.get_mid_market_price()
              for orderbook in orderbooks}
    reverse_prices = {
        '_'.join(product.split('_')[::-1]): 1 / prices[product]
        for product in prices.keys()
    }
    prices.update(reverse_prices)
    return prices


def topological_sort(orders: List[Tuple[str, str, Decimal]]) -> (
        List[Tuple[str, str, Decimal]]):
    """
    sort orders topologically
    """
    product_to_order = {'_'.join(order[:2]): order for order in orders}
    currencies = set([currency for order in orders for currency in order[:2]])
    graph = defaultdict(set)
    for order in orders:
        graph[order[0]].add(order[1])
    currencies_to = {currency_to for currencies_to in graph.values()
                     for currency_to in currencies_to}
    graph['start'] = currencies - currencies_to
    currencies = dfs(graph, set(), 'start')[::-1][1:]
    # without start
    orders = []
    for currency_from in currencies:
        for currency_to in graph[currency_from]:
            product = '_'.join([currency_from, currency_to])
            orders.append(product_to_order[product])
    return orders


def dfs(graph, visited, start):
    visited.add(start)
    nexts = []
    for currency in graph[start]:
        if currency in visited:
            continue
        nexts += dfs(graph, visited, currency)
    nexts.append(start)
    return nexts
