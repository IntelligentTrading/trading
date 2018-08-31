import tasks
from decimal import Decimal
from celery.result import AsyncResult
from rest_framework.views import APIView
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, PermissionDenied
from webserver.api_exceptions import WeightsSumGreaterThanOne


from webserver.utils import get_portfolio


from webserver.decorators import with_valid_api_key, \
    initialize_exchange


class HealthCkeckView(APIView):
    def get(self, request):
        return Response({"status": "ok"})


class PortfolioView(APIView):
    parser_classes = (JSONParser,)

    @with_valid_api_key
    @initialize_exchange
    def post(self, request, exchange, params):
        response = {params['name']: get_portfolio(exchange)}
        return Response(response)

    @with_valid_api_key
    @initialize_exchange
    def put(self, request, exchange, params):

        allocations = params['allocations']
        total_weight = sum(Decimal(allocation['portion'])
                           for allocation in allocations)
        if total_weight > 1:
            raise WeightsSumGreaterThanOne

        found_btc = False
        for allocation in allocations:
            if allocation['coin'] != 'BTC':
                continue
            allocation['portion'] += Decimal('1') - total_weight
            found_btc = True

        if not found_btc:
            allocations += [{'coin': 'BTC',
                             'portion': Decimal('1') - total_weight}]

        weights = {
            allocation['coin']: Decimal(allocation['portion']).to_eng_string()
            for allocation in allocations}

        result = tasks.rebalance_task.delay(request.data,
                                            request.user.api_key,
                                            weights)

        return Response({
            "status": "target allocations queued for processing",
            "portfolio_processing_request":
                "/api/portfolio_process/{}".format(result.id),
            "retry_after": 25000
        })


class ProcessingView(APIView):
    parser_classes = (JSONParser,)

    @with_valid_api_key
    def post(self, request, process_id):
        result = AsyncResult(process_id, app=tasks.app)

        if result.state == "PENDING":
            raise NotFound

        if result.result["api_key"] != request.user.api_key:
            raise PermissionDenied

        if result.status == "STARTED":
            return Response({
                "status": "processing in progress",
                "portfolio_processing_request":
                    "/api/portfolio_process/{}".format(result.id),
                "retry_after": 12000
            })

        response = result.result
        response.pop('api_key')
        return Response(response)
