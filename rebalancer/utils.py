from internals.orderbook import OrderBook
from typing import List, Dict, Tuple
from decimal import Decimal
from collections import defaultdict


def rebalance_orders(initial_weights: Dict[str, Decimal],
                     final_weights: Dict[str, Decimal]) -> (
        List[Tuple[str, str, Decimal]]):
    """
    :param initial_weights: weights before rebalance
    :param final_weights: weights after rebalance
    :return: List of orders, each order is list of length 3,
                             currency from, currency to, quantity_in_base
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


def get_price_estimates_from_orderbooks(
        orderbooks: List[OrderBook], base: str) -> Dict[str, Decimal]:
    """
    get currency to price dictionary
    """
    currency_pair_prices = get_prices_from_orderbooks(orderbooks)
    graph = {}

    for (currency_from, currencies_to), price in currency_pair_prices.items():
        if currency_from not in graph:
            graph[currency_from] = {}
        graph[currency_from][currencies_to] = -price.log10()

    dists = bfs(graph, base)
    dists = {k: Decimal(10) ** v for k, v in dists.items()}
    return dists


def get_mid_prices_from_orderbooks(orderbooks: List[OrderBook]) -> (
        Dict[str, Decimal]):
    """
    get product to price dictionary (with reverse products)
    """
    prices = {orderbook.product: orderbook.get_mid_market_price()
              for orderbook in orderbooks}
    reverse_prices = {
        '_'.join(product.split('_')[::-1]): 1 / prices[product]
        for product in prices.keys()
    }
    prices.update(reverse_prices)
    return prices


def get_prices_from_orderbooks(orderbooks: List[OrderBook]) -> (
        Dict[Tuple[str, str], Decimal]):
    """
    get product to price dictionary (with reverse products)
    """
    prices = {tuple(orderbook.product.split('_')): orderbook.get_wall_bid()
              for orderbook in orderbooks}
    reverse_prices = {
        tuple(orderbook.product.split('_')[::-1]): (
            1 / orderbook.get_wall_ask())
        for orderbook in orderbooks
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


def bfs(graph, start):
    queue = [start]
    dists = {start: 0}
    i = 0
    while i < len(queue):
        current_vertex = queue[i]
        for v, w in graph[current_vertex].items():
            if v in dists and dists[v] < dists[current_vertex] + w:
                continue
            if v not in dists:
                queue.append(v)
            dists[v] = dists[current_vertex] + w
        i += 1

    return dists
