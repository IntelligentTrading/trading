from rest_framework.exceptions import APIException


class ExchangeNotSupported(APIException):
    status_code = 418
    default_detail = 'Only Binance exchange support is available at this time.'
    default_code = 'i_am_a_teapot'


class MustProvideSingleExchange(APIException):
    status_code = 418
    default_detail = 'You have to provide credentials for exactly one exchange'
    default_code = 'i_am_a_teapot'


class MustProvideBinanceCredentials(APIException):
    status_code = 400
    default_detail = ('YOu must provide "api_key" and "secret_key" to'
                      'authenticate with the Exchange')
    default_code = 'Bad_Request'


class WeightsSumGreaterThanOne(APIException):
    status_code = 400
    default_detail = 'Allocations sum is greater than 1.0'
    default_code = 'Bad_Request'


class BinanceException(APIException):
    def __init__(self, exception):
        self.detail = str(exception)

    status_code = 400
    default_code = 'Bad_Request'
