import logging
from strategies.cross_exchange import find_arbitrage_opportunities
from config.settings import MIN_PROFIT_THRESHOLD_USD, MIN_PROFIT_THRESHOLD_PERCENT

logging.basicConfig(level=logging.INFO)

def test_arbitrage():
    print(f"🧪 Threshold profit: ${MIN_PROFIT_THRESHOLD_USD} atau {MIN_PROFIT_THRESHOLD_PERCENT*100}%")

    prices = {
        'binance': {'BTC': 30000.0, 'XRP': 0.90, 'SHIB': 0.00003, 'BNB': 400.0},
        'indodax': {'BTC': 29900.0, 'XRP': 0.85, 'SHIB': 0.000028, 'BNB': 390.0},
        'kucoin': {'BTC': 30010.0, 'XRP': 0.92, 'SHIB': 0.000031, 'BNB': 405.0}
    }

    class DummyExchange:
        def __init__(self, name):
            self._name = name
        
        @property
        def __class__(self):
            class DummyClass:
                @property
                def __name__(self_inner):
                    return self._name
            return DummyClass()
        
        def get_base_currency(self):
            return "USDT"
        
        def fetch_balance(self):
            return {
                "USDT": {"free": 1000},
                "BTC": {"free": 10},
                "XRP": {"free": 1000},
                "SHIB": {"free": 1000000},
                "BNB": {"free": 100}
            }

    exchanges = [DummyExchange("binance"), DummyExchange("indodax"), DummyExchange("kucoin")]

    opportunities = find_arbitrage_opportunities(prices, exchanges)

    if not opportunities:
        print("❌ Tidak ditemukan peluang arbitrase dari mock test")
    else:
        print(f"✅ Ditemukan {len(opportunities)} peluang arbitrase")

if __name__ == "__main__":
    test_arbitrage()
