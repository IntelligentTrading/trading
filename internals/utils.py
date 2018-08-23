def binance_product_to_currencies(product: str) -> [str, str]:
    for c in 'USDT BTC BNB ETH'.split():
        if product.endswith(c):
            return product[:-len(c)], c
