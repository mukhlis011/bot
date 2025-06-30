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
    
    def collect_prices(self):
        prices = {}
        usd_to_idr = get_usd_to_idr_rate()
        
        for exchange in self.exchanges:
            exchange_name = exchange.__class__.__name__.lower()
            prices[exchange_name] = {}
            
            for symbol in self.symbols:
                try:
                    price = exchange.fetch_ticker(symbol)
                    
                    # Periksa jika harga tidak valid
                    if price is None or price <= 0:
                        logger.warning(f"⚠️ Harga {symbol} di {exchange_name} tidak valid: {price}")
                        prices[exchange_name][symbol] = 0.0
                        continue
                    
                    base_currency = exchange.get_base_currency()
                    
                    # Konversi ke USD jika perlu
                    if base_currency == "IDR":
                        price = price / usd_to_idr
                    
                    prices[exchange_name][symbol] = price
                    logger.info(f"📊 {exchange_name.upper()} {symbol}: ${price:.6f} USD")
                    
                except Exception as e:
                    logger.error(f"❌ Gagal ambil harga {symbol} dari {exchange_name}: {e}")
                    prices[exchange_name][symbol] = 0.0
        
        return prices