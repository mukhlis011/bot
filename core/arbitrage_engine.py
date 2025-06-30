from strategies.cross_exchange import find_arbitrage_opportunities
from utils.logger import logger
from utils.helpers import calculate_net_profit, get_usd_to_idr_rate

class ArbitrageEngine:
    def __init__(self, price_collector, exchanges):
        self.price_collector = price_collector
        self.exchanges = exchanges

    def run(self):
        try:
            prices = self.price_collector.collect_prices()
            opportunities = find_arbitrage_opportunities(prices, self.exchanges)

            # Tambahkan logging selisih dan profit
            usd_to_idr = get_usd_to_idr_rate()
            for opp in opportunities:
                symbol = opp['symbol']
                buy_ex = opp['buy_exchange']
                sell_ex = opp['sell_exchange']
                buy_price = opp['buy_price']
                sell_price = opp['sell_price']
                
                spread = sell_price - buy_price
                net = calculate_net_profit(symbol, buy_price, sell_price, buy_ex, sell_ex)['net_profit']
                
                feetotal = spread - net + spread  # perkiraan total fee (perkiraan sederhana)
                profit_label = "Layak" if net > 0 else "Tidak Layak"

                logger.info(f"{symbol} | {buy_ex.upper()} ${buy_price:.2f} | "
                            f"{sell_ex.upper()} ${sell_price:.2f} | FeeTotal±: ${abs(feetotal):.2f} | "
                            f"Profit±: ${net:.2f} | {profit_label}")

            return opportunities
        except Exception as e:
            logger.error(f"🚨 Error di ArbitrageEngine: {e}")
            return []
