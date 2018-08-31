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
        resources, price_estimates).quantize(Decimal('1e-8'))

    allocations = []
    for currency, quantity in resources.items():
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
