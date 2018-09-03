import init_django  # noqa
import os
import time
import celery

from rebalancer.limit_order_rebalancer import limit_order_rebalance
from rebalancer.market_order_rebalancer import market_order_rebalance_and_save
from webserver.decorators import initialize_exchange
from webserver.utils import get_portfolio


app = celery.Celery('rebalance')

app.conf.update(broker_url=os.environ['REDIS_URL'],
                result_backend=os.environ['REDIS_URL'],
                task_serializer='json',
                result_serializer='json',
                accept_content=['json'])


REBALANCING_ALGORITHM = {
    'MARKET': market_order_rebalance_and_save,
    'LIMIT': limit_order_rebalance
}


@app.task(bind=True)
def rebalance_task(self, request, api_key, weights):

    @initialize_exchange
    def rebalance(this, request, exchange, params):

        start_time = time.time()
        self.update_state(
            None,
            "STARTED",
            {
                "start_time": start_time,
                "api_key": api_key
            }
        )

        REBALANCING_ALGORITHM[params.get('type', 'market').upper()](
            api_key, exchange, weights)

        portfolio = get_portfolio(exchange)
        delta_t = (time.time() - start_time) * 1000

        return {params['name']: portfolio,
                'api_key': api_key,
                'status': "processing complete in {0:.0f}ms".format(delta_t)}

    return rebalance(self, request)
