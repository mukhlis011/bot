import os
import hmac
import hashlib
import requests
import time
import logging
from urllib.parse import urlencode
from .exchange_interface import Exchange

logger = logging.getLogger(__name__)

class Binance(Exchange):
    BASE_URL = "https://api.binance.com"

    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.api_secret = os.getenv("BINANCE_SECRET_KEY")
        if not self.api_key or not self.api_secret:
            raise ValueError("Binance API key dan secret wajib di-set")
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})
        logger.info("✅ Binance client initialized")

    def get_base_currency(self):
        return "USDT"

    def _signed_request(self, method, endpoint, params=None):
        if params is None:
            params = {}
        
        params['timestamp'] = int(time.time() * 1000)
        query_string = urlencode(params, doseq=True)
        
        # Buat signature
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        params['signature'] = signature
        
        url = f"{self.BASE_URL}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params, timeout=10)
            else:
                response = self.session.post(url, data=params, timeout=10)
            
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Request gagal: {e}, URL: {url}, Params: {params}")
            return None

    def fetch_ticker(self, symbol):
        try:
            symbol_pair = symbol.upper() + "USDT"
            params = {"symbol": symbol_pair}
            data = self._signed_request("GET", "/api/v3/ticker/price", params)
            if data is None:
                return 0.0
            return float(data["price"])
        except Exception as e:
            logger.error(f"❌ Gagal fetch ticker {symbol}: {e}")
            return 0.0

    def fetch_balance(self):
        try:
            data = self._signed_request("GET", "/api/v3/account")
            if data is None:
                return {}
            return {item['asset']: {'free': float(item['free'])} for item in data['balances']}
        except Exception as e:
            logger.error(f"❌ Gagal fetch balance: {e}")
            return {}

    def transfer_coin(self, symbol, amount, address, tag=None, network=None):
        params = {
            'asset': symbol.upper(),
            'address': address,
            'amount': amount,
            'timestamp': int(time.time() * 1000)
        }
        
        if tag:
            params['addressTag'] = tag
        if network:
            params['network'] = network
        
        try:
            data = self._signed_request("POST", "/sapi/v1/capital/withdraw/apply", params)
            return data is not None and 'id' in data
        except Exception as e:
            logger.error(f"❌ Gagal transfer: {e}")
            return False