import unittest
from internals.utils import binance_product_to_currencies


class UtilsTester(unittest.TestCase):
    def test_binance_product_to_currencies(self):
        gdax_products = ['BTC_USDT',
                         'ETH_USDT',
                         'ETH_BTC',
                         'LTC_BTC',
                         'ADA_BNB',
                         'ADA_BTC',
                         'TUSD_USDT',
                         'VET_ETH',
                         'EOS_ETH']
        currency_pairs = [p.split('_') for p in gdax_products]
        binance_products = [''.join(p) for p in currency_pairs]
        binance_currency_pairs = [
            binance_product_to_currencies(p) for p in binance_products]
        for real_pair, derived_pair in zip(
                currency_pairs, binance_currency_pairs):
            self.assertEqual(len(derived_pair), 2)
            self.assertEqual(real_pair[0], derived_pair[0])
            self.assertEqual(real_pair[1], derived_pair[1])
