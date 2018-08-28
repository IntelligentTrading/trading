from rest_framework.exceptions import APIException


class ExchangeNotSupported(APIException):
    status_code = 418
    default_detail = 'Only Binance exchange support is available at this time.'
    default_code = 'i_am_a_teapot'


class WeightsSumGreaterThanOne(APIException):
    status_code = 400
    default_detail = 'Allocations sum is greater than 1.0'
    default_code = 'Bad_Request'
