from strategies.cross_exchange import find_arbitrage_opportunities
from utils.logger import logger

class ArbitrageEngine:
    def __init__(self, price_collector, exchanges):
        self.price_collector = price_collector
        self.exchanges = exchanges

    def run(self):
        try:
            prices = self.price_collector.collect_prices()
            return find_arbitrage_opportunities(prices, self.exchanges)
        except Exception as e:
            logger.error(f"🚨 Error di ArbitrageEngine: {e}")
            return []