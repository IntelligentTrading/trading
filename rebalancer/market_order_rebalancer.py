from rebalancer.utils import rebalance_orders, topological_sort, \
    get_total_fee, parse_order, pre_rebalance
from typing import Dict, List
from exchange.exchange import Exchange
from decimal import Decimal
from webserver.models import Statistics


def market_order_rebalance_and_save(user,
                                    exchange: Exchange,
                                    weights: Dict[str, Decimal],
                                    base: str='USDT'):
    rets = market_order_rebalance(exchange, weights, base)
    summaries = create_order_statistics_objects(rets, user)
    Statistics.objects.bulk_create(summaries)


def market_order_rebalance(exchange: Exchange,
                           weights: Dict[str, Decimal],
                           base: str='USDT'):
    (products, resources, orderbooks, price_estimates,
     portfolio_value, initial_weights,
     spread_fees) = pre_rebalance(exchange, weights, base)

    fees = {product: exchange.get_taker_fee(product)
            for product in products}

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
                ret_orders.append(ret_order)
                break
        if ret_order is None or isinstance(ret_order, Exception):
            continue
        ret_order['mid_market_price'] = orderbooks[
            order.product].get_mid_market_price()

    return ret_orders


def create_order_statistics_objects(order_responses, user) -> List[Statistics]:
    """
    :param order_responses: responses from market
    :return: Statistics objects
    """
    statistics = []
    for order_response in order_responses:
        if order_response is None:
            continue
        _, base = order_response['product'].split('_')
        price_estimates = order_response['price_estimates']
        fee = 0
        for k, v in order_response.items():
            if k.startswith('commission_'):
                fee += price_estimates[k[len('commission_'):]] * v
        fee /= price_estimates[base]
        statistic = Statistics(
            user=user,
            mid_market_price=float(order_response['mid_market_price']),
            average_exec_price=float(order_response['mean_price']),
            volume=float(order_response['mean_price'] *
                         order_response['executed_quantity'] + fee),
            pair=order_response['product'],
            fee=float(fee),
            action=order_response['side'].lower())
        statistics.append(statistic)
    return statistics
