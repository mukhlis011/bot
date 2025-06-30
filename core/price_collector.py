import os
import logging
from utils.helpers import get_usd_to_idr_rate

logger = logging.getLogger(__name__)

class PriceCollector:
    def __init__(self, exchanges):
        self.exchanges = exchanges
        self.symbols = self.get_supported_symbols()

    def get_supported_symbols(self):
        return os.getenv('SUPPORTED_SYMBOLS', 'BTC,XRP,SHIB,BNB').split(',')

    def get_symbol_for_exchange(self, exchange_name, symbol):
        symbol = symbol.strip()
        if exchange_name == 'indodax':
            return symbol.lower()
        elif exchange_name == 'binance':
            if symbol.upper().endswith('USDT'):
                return symbol.upper()
            return symbol.upper() + 'USDT'
        elif exchange_name == 'kucoin':
            if symbol.upper().endswith('-USDT'):
                return symbol.upper()
            return symbol.upper() + '-USDT'
        else:
            return symbol

    def collect_prices(self):
        prices = {}
        usd_to_idr = get_usd_to_idr_rate()
        
        for exchange in self.exchanges:
            exchange_name = exchange.__class__.__name__.lower()
            prices[exchange_name] = {}

            for symbol in self.symbols:
                try:
                    symbol_for_ex = self.get_symbol_for_exchange(exchange_name, symbol)
                    price = exchange.fetch_ticker(symbol_for_ex)

                    if price is None or price <= 0:
                        logger.warning(f"⚠️ Harga {symbol} di {exchange_name} tidak valid: {price}")
                        prices[exchange_name][symbol] = 0.0
                        continue

                    base_currency = exchange.get_base_currency()

                    if base_currency == "IDR":
                        price = price / usd_to_idr

                    prices[exchange_name][symbol] = price
                    logger.info(f"📊 {exchange_name.upper()} {symbol}: ${price:.6f} USD")

                except Exception as e:
                    logger.error(f"❌ Gagal ambil harga {symbol} dari {exchange_name}: {e}")
                    prices[exchange_name][symbol] = 0.0
        
        return prices
