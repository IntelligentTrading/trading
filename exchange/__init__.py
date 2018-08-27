from exchange.exchange import Exchange
from exchange.binance import Binance
from exchange.coinbasepro import CoinbasePro


def get_exchange_by_name(name: str) -> Exchange:
    name = name.upper()
    return {"BINANCE": Binance, "COINBASEPRO": CoinbasePro}[name]
