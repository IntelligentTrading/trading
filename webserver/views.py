import binance
import ujson as json
from decimal import Decimal, ROUND_DOWN

from django.http import JsonResponse, HttpResponse

from webserver.decorators import with_valid_api_key
from exchange import get_exchange_by_name
from rebalancer.utils import get_price_estimates_from_orderbooks, \
    get_weights_from_resources, get_portfolio_value_from_resources

from rest_framework.views import APIView
from rest_framework.parsers import JSONParser


class HealthCkeckView(APIView):
    def get(self, request):
        return JsonResponse({"status": "ok"})


class PortfolioView(APIView):

    parser_classes = (JSONParser,)

    @with_valid_api_key
    def post(self, request):

        response = {}
        for name, keys in request.data.items():

            if name.upper() != 'BINANCE':
                return HttpResponse(
                    json.dumps(
                        {"error": "only binance exchange support "
                                  "available at this time"}),
                    content_type="application/json", status=418)

            exchange_class = get_exchange_by_name(name)
            api_key = keys['api_key']
            api_secret = keys['secret_key']

            try:
                exchange = exchange_class(api_key, api_secret)
                response[name] = get_portfolio(exchange)
            except binance.exceptions.BinanceAPIException:
                return HttpResponse(
                    json.dumps({"error": "exchange API keys invalid"}),
                    content_type="application/json", status=404)

        return JsonResponse(response)


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
