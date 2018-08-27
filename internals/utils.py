from decimal import Decimal, ROUND_DOWN, ROUND_UP


def binance_product_to_currencies(product: str) -> [str, str]:
    for c in 'USDT BTC BNB ETH'.split():
        if product.endswith(c):
            return product[:-len(c)], c


def quantize(x, precision, down=True):
    x = Decimal(x)
    precision = Decimal(precision)
    rounding = ROUND_DOWN if down else ROUND_UP
    return x.quantize(precision.normalize(), rounding=rounding)
