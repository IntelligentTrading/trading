from internals.orderbook import OrderBook
from typing import List, Dict, Tuple, Set
from decimal import Decimal
from collections import defaultdict
from internals.order import Order
from internals.enums import OrderType, OrderAction
from networkx import digraph
from networkx import flow
from networkx.exception import NetworkXUnfeasible
from exchange.exchange import Exchange


def rebalance_orders(initial_weights: Dict[str, Decimal],
                     final_weights: Dict[str, Decimal],
                     fees: Dict[str, Decimal],
                     precision: Decimal=Decimal('1e-8')) -> (
        List[Tuple[str, str, Decimal]]):
    """
    :param initial_weights: weights before rebalance
    :param final_weights: weights after rebalance
    :param fee: dict from product to fee
    :return: List of orders, each order is list of length 3,
                             currency from, currency to, quantity_in_base
                                                (might be product, quantity)
    """
    parsed_fees = {tuple(k.split('_')): v for k, v in fees.items()}
    digraph = create_flow_digraph(
        initial_weights, final_weights, parsed_fees, precision=precision)
    try:
        orders_to_make = flow.min_cost_flow(digraph)
    except NetworkXUnfeasible as error:
        return error
    orders = []
    for currency_from, dct in orders_to_make.items():
        if currency_from == 'start':
            continue
        for currency_to, quantity_in_base in dct.items():
            if currency_to == 'end' or quantity_in_base < 1e-18:
                continue
            orders.append((currency_from, currency_to,
                           Decimal(quantity_in_base) * precision))
    return orders


def create_flow_digraph(initial_weights: Dict[str, Decimal],
                        final_weights: Dict[str, Decimal],
                        total_fees: Dict[Tuple[str, str], Decimal],
                        precision: Decimal=Decimal('1e-8')) -> digraph.DiGraph:
    currencies = set(initial_weights.keys()) | set(final_weights.keys())
    start = 'start'
    end = 'end'
    inv_precision = 1 / precision
    w1 = {k: int(Decimal(v) * inv_precision)
          for k, v in initial_weights.items()}
    w2 = {k: int(Decimal(v) * inv_precision) for k, v in final_weights.items()}
    inv_precision = float(inv_precision)
    demand_from = sum(w1.values())
    demand_to = sum(w2.values())
    demand = min(demand_to, demand_from)
    graph = digraph.DiGraph()

    graph.add_nodes_from(currencies, demand=0.)
    graph.add_node(start, demand=-demand)
    graph.add_node(end, demand=demand)

    for currency, capacity in w1.items():
        graph.add_edge(start, currency, capacity=capacity, weight=0)

    for currency, capacity in w2.items():
        graph.add_edge(currency, end, capacity=capacity, weight=0)

    for (c1, c2), fee in total_fees.items():
        graph.add_edge(c1, c2,
                       capacity=float('inf'),
                       weight=-int(float(fee.log10()) * inv_precision))
        graph.add_edge(c2, c1,
                       capacity=float('inf'),
                       weight=-int(float(fee.log10()) * inv_precision))
    return graph


def get_weights_from_resources(
        resources: Dict[str, Decimal],
        prices: Dict[str, Decimal]) -> Dict[str, Decimal]:
    resources_in_base = {
        currency: resources[currency] * prices[currency]
        for currency in resources if currency in prices
    }
    portfolio_value = sum(resources_in_base.values())
    weights = {
        currency: resources_in_base[currency] / portfolio_value
        for currency in resources_in_base
    }
    return weights


def get_portfolio_value_from_resources(
        resources: Dict[str, Decimal],
        prices: Dict[str, Decimal]) -> Decimal:
    resources_in_base = {
        currency: resources[currency] * prices.get(currency, Decimal('0'))
        for currency in resources
    }
    portfolio_value = sum(resources_in_base.values())
    return portfolio_value


def get_price_estimates_from_orderbooks(
        orderbooks: List[OrderBook], base: str) -> Dict[str, Decimal]:
    """
    get currency to price dictionary
    """
    currency_pair_prices = get_mid_prices_from_orderbooks(orderbooks)
    graph = {}

    for product, price in currency_pair_prices.items():
        currency_from, currencies_to = product.split('_')
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


def dfs(graph: Dict[str, Set[str]], visited: Set[str], start: str)-> List[str]:
    visited.add(start)
    nexts = []
    for currency in graph[start]:
        if currency in visited:
            continue
        nexts += dfs(graph, visited, currency)
    nexts.append(start)
    return nexts


def bfs(graph: Dict[str, Dict[str, Decimal]], start: str)-> Dict[str, Decimal]:
    queue = [[start, 0]]
    dists = {start: [0, 0]}
    i = 0
    while i < len(queue):
        current_vertex, depth = queue[i]
        for v, w in graph[current_vertex].items():
            if v in dists and (dists[v][1] != dists[current_vertex][1] or (
                    dists[v][0] < dists[current_vertex][0] + w)):
                continue
            if v not in dists:
                queue.append([v, depth + 1])
            dists[v] = [dists[current_vertex][0] + w, depth + 1]
        i += 1

    return {k: v[0] for k, v in dists.items()}


def spread_to_fee(orderbook):
    wall_ask = orderbook.get_wall_ask()
    wall_bid = orderbook.get_wall_bid()
    return 1 - (wall_bid / wall_ask).sqrt()


def get_total_fee(*fees):
    p = 1
    for fee in fees:
        p *= 1 - fee

    return 1 - p


def parse_order(order: Tuple[str, str, Decimal],
                products: List[str],
                price_estimates: Dict[str, Decimal],
                base: str,
                _type: OrderType=OrderType.MARKET,
                price: Decimal=None):
    assert (price is None) == (_type == OrderType.MARKET)
    product = [product for product in products if product == '_'.join(
        order[:2]) or product == '_'.join(order[:2][::-1])][0]

    quantity_in_base = order[2]
    quantity = quantity_in_base * (
        price_estimates[base] / price_estimates[product.split('_')[0]])

    if product == '_'.join(order[:2]):
        side = OrderAction.SELL
    else:
        side = OrderAction.BUY

    return Order(product, _type, side, quantity, price)


def pre_rebalance(exchange: Exchange,
                  weights: Dict[str, Decimal],
                  base: str='USDT'):
    resources = exchange.get_resources()
    currencies = (exchange.through_trade_currencies() |
                  set(list(resources.keys())) | set(list(weights.keys())))
    all_possible_products = ['_'.join([i, j])
                             for i in currencies
                             for j in currencies]

    orderbooks = exchange.get_orderbooks(all_possible_products)
    # getting all ordebrooks and filtering out orderbooks,
    # that use other currencies
    products = set(orderbook.product for orderbook in orderbooks)

    price_estimates = get_price_estimates_from_orderbooks(orderbooks, base)

    not_existing_currencies = []
    for cur in weights.keys():
        if price_estimates.get(cur, Decimal('0')) == Decimal('0'):
            not_existing_currencies.append(cur)
    if not_existing_currencies:
        return not_existing_currencies

    initial_weights = get_weights_from_resources(
        resources, price_estimates)
    portfolio_value = get_portfolio_value_from_resources(
        resources, price_estimates)
    orderbooks = {orderbook.product: orderbook
                  for orderbook in orderbooks}

    spread_fees = {product: spread_to_fee(orderbook)
                   for product, orderbook in orderbooks.items()}

    return (products, resources, orderbooks, price_estimates,
            portfolio_value, initial_weights, spread_fees)
