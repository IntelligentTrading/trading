import json
import logging
from decimal import Decimal, ROUND_DOWN

from rebalancer.utils import get_price_estimates_from_orderbooks, \
    get_weights_from_resources, get_portfolio_value_from_resources


def get_portfolio(exchange):
    resources = exchange.get_resources()
    resources = {k: v for k, v in resources.items() if v > Decimal(1e-8)}
    orderbooks = exchange.get_orderbooks()

    price_estimates = get_price_estimates_from_orderbooks(orderbooks, 'BTC')

    weights = get_weights_from_resources(resources, price_estimates)

    portfolio_value = get_portfolio_value_from_resources(
        resources, price_estimates)

    if portfolio_value == 0:
        return {"value": portfolio_value, "allocations": []}

    portfolio_value = portfolio_value.quantize(Decimal('1e-8'))

    allocations = []
    for currency, quantity in resources.items():
        if not currency in weights:
            logging.critical(f"{currency} is not the proper ticker symbol")
            continue

        allocation = {
            "coin": currency,
            "amount": quantity,
            "portion": weights[currency].quantize(Decimal('1e-4'), ROUND_DOWN)
        }
        if allocation['portion'] > Decimal('1e-4'):
            allocations.append(allocation)

    allocations_sum = sum([a["portion"] for a in allocations])
    assert 1 >= allocations_sum > 0.99

    return {"value": portfolio_value, "allocations": allocations}


def dict_replace(string, dictionary):
    for key, value in dictionary.items():
        string = string.replace(key, value)
    return string


def user_has_unfinished_tasks(tasks, api_key):
    """
    checks if task with api_key exists in tasks
    :param tasks: Dict[worker, List[job]],
                  for example celery.Celery().control.inspect().active()
    :param api_key: string, api key of user
    :return: None if such job doesn't exist,
             and Tuple(job, task arguments) otherwise
    """
    if tasks is None:
        return
    for worker, jobs in tasks.items():
        for job in jobs:
            args = json.loads(dict_replace(
                job['args'], {'(': '[', ')': ']', '...': '', "'": '"'}))
            # the arguments, which were sent to task
            if args[1] == api_key:
                return job, args
