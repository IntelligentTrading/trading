from functools import wraps

from webserver.models import User
from django.utils.decorators import method_decorator
from django.core.exceptions import PermissionDenied

from exchange import get_exchange_by_name
import binance
from .api_exceptions import MustProvideSingleExchange
from .api_exceptions import ExchangeNotSupported
from .api_exceptions import MustProvideBinanceCredentials
from .api_exceptions import BinanceException


@method_decorator
def initialize_exchange(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if len(request.data) != 1:
            raise MustProvideSingleExchange

        [(exchange_name, info)] = request.data.items()

        if exchange_name.upper() != 'BINANCE':
            raise ExchangeNotSupported

        exchange_class = get_exchange_by_name(exchange_name)

        if set(['api_key', 'secret_key']) - info.keys():
            raise MustProvideBinanceCredentials

        api_key = info.pop('api_key')
        api_secret = info.pop('secret_key')
        exchange = exchange_class(api_key, api_secret)
        try:
            exchange.get_resources()
        except binance.exceptions.BinanceAPIException as e:
            # TODO: move get_resources else
            raise BinanceException(e)
        info['name'] = exchange_name
        return view_func(request, exchange, info, *args, **kwargs)
    return _wrapped_view


@method_decorator
def with_valid_api_key(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if 'api_key' not in request.data:
            raise PermissionDenied
        api_key = request.data.pop('api_key')
        try:
            request.user = User.objects.get(api_key=api_key)
        except User.DoesNotExist:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view
