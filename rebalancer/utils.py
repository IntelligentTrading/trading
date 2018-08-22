from internals.order import Order
from internals.orderbook import OrderBook
from typing import List, Dict
from decimal import Decimal


def rebalance_orders(initial_weights: Dict[str, Decimal],
                     final_weights: Dict[str, Decimal],
                     prices: Dict[str, Decimal]) -> (
        List[List[str, str, Decimal]]):
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
    raise NotImplementedError


def get_prices_from_orderbooks(orderbook: List[OrderBook]):
    raise NotImplementedError


def topological_sort(orders: List[Order]) -> List[Order]:
    """
    sort orders topologically
    """
    raise NotImplementedError
