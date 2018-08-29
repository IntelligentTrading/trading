from decimal import Decimal, ROUND_DOWN

from webserver.decorators import with_valid_api_key, \
    initialize_exchange
from rebalancer.utils import get_price_estimates_from_orderbooks, \
    get_weights_from_resources, get_portfolio_value_from_resources
from rebalancer.market_order_rebalancer import market_order_rebalance
from rebalancer.limit_order_rebalancer import limit_order_rebalance
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from .api_exceptions import WeightsSumGreaterThanOne


REBALANCING_ALGORITHM = {
    'MARKET': market_order_rebalance,
    'LIMIT': limit_order_rebalance
}


class HealthCkeckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class PortfolioView(APIView):

    parser_classes = (JSONParser,)

    @with_valid_api_key
    @initialize_exchange
    def post(self, request, exchange, params):
        response = {}
        response[params['name']] = get_portfolio(exchange)
        return Response(response)

    @with_valid_api_key
    @initialize_exchange
    def put(self, request, exchange, params):
        response = {}
        allocations = params['allocations']
        total_weight = sum(Decimal(allocation['portion'])
                           for allocation in allocations)
        if total_weight > 1:
            raise WeightsSumGreaterThanOne

        found_BTC = False
        for allocation in allocations:
            if allocation['coin'] != 'BTC':
                continue
            allocation['portion'] += Decimal('1') - total_weight
            found_BTC = True

        if not found_BTC:
            allocations += [{'coin': 'BTC',
                             'portion': Decimal('1') - total_weight}]

        weights = {allocation['coin']: allocation['portion']
                   for allocation in allocations}

        ret = REBALANCING_ALGORITHM[params.get('type', 'market').upper()](
            exchange, weights)
        response[params['name']] = ret

        return Response(response)


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
