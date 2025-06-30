import os
import requests
from utils.logger import logger

class Bybit:
    def __init__(self):
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.api_secret = os.getenv("BYBIT_SECRET_KEY")

        if not self.api_key or not self.api_secret:
            raise ValueError("Bybit API key dan secret wajib di-set di environment variables")

        self.base_url = "https://api.bybit.com"

        logger.info("✅ Bybit client initialized successfully")

    def fetch_ticker(self, symbol):
        """
        Fetch harga terbaru untuk simbol tertentu.
        Mapping simbol standar ke pair Bybit.
        Bybit biasanya pakai simbol seperti BTCUSDT (no slash).
        """
        try:
            # Mapping symbol ke pair Bybit
            pair = symbol.upper() + "USDT"  # contoh: BTC -> BTCUSDT

            url = f"{self.base_url}/v2/public/tickers?symbol={pair}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data['ret_code'] != 0 or not data.get('result'):
                logger.error(f"🚨 Response error from Bybit API: {data}")
                return None

            ticker = data['result'][0]
            last_price = float(ticker['last_price'])
            return last_price
        except Exception as e:
            logger.error(f"🚨 Gagal fetch ticker Bybit {symbol}: {e}")
            return None

    def fetch_balance(self):
        """
        Contoh dummy balance fetch, perlu diimplementasi sesuai API Bybit v2 atau v5.
        Biasanya perlu auth signature, contoh minimal:
        return {'USDT': {'free': 1000.0}, 'BTC': {'free': 0.5}}
        """
        # TODO: Implement authenticated API call to get balances
        logger.warning("⚠️ fetch_balance Bybit belum diimplementasi, returning dummy balance")
        return {
            'USDT': {'free': 1000.0},
            'BTC': {'free': 0.1},
            'BNB': {'free': 0.0},
            'XRP': {'free': 0.0},
        }
