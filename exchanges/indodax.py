import os
import time
import hashlib
import hmac
import requests
import logging
from .exchange_interface import Exchange

logger = logging.getLogger(__name__)

class Indodax(Exchange):
    BASE_URL = "https://indodax.com"
    TAPI_URL = "https://indodax.com/tapi"

    def __init__(self):
        self.api_key = os.getenv("INDODAX_API_KEY")
        self.secret_key = os.getenv("INDODAX_SECRET_KEY")
        if not self.api_key or not self.secret_key:
            raise ValueError("Indodax API key dan secret wajib di-set")
        self.session = requests.Session()
        logger.info("✅ Indodax client initialized")

    def get_base_currency(self):
        return "IDR"

    def _generate_signature(self, params):
        query_string = '&'.join([f"{key}={params[key]}" for key in sorted(params)])
        return hmac.new(
            self.secret_key.encode('utf-8'),
            query_string.encode('utf-8'),
            hashlib.sha512
        ).hexdigest()

    def fetch_ticker(self, symbol):
        pair = f"{symbol.lower()}_idr"
        try:
            response = self.session.get(f"{self.BASE_URL}/api/ticker/{pair}", timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Perbaikan: Pastikan struktur respons benar
            if 'ticker' in data and 'last' in data['ticker']:
                return float(data['ticker']['last'])
            else:
                logger.error(f"❌ Format respons tidak valid: {data}")
                return 0.0
        except Exception as e:
            logger.error(f"❌ Gagal fetch ticker {pair}: {e}")
            return 0.0

    def fetch_balance(self):
        params = {'method': 'getInfo', 'timestamp': int(time.time() * 1000)}
        headers = {'Key': self.api_key, 'Sign': self._generate_signature(params)}
        
        try:
            response = self.session.post(self.TAPI_URL, data=params, headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get('return', {}).get('balance', {})
        except Exception as e:
            logger.error(f"❌ Gagal fetch balance: {e}")
            return {}

    def transfer_coin(self, symbol, amount, address, tag=None, network=None):
        params = {
            'method': 'withdrawCoin',
            'timestamp': int(time.time() * 1000),
            'currency': symbol.upper(),
            'withdraw_address': address,
            'withdraw_amount': amount,
            'withdraw_memo': tag or ''
        }
        
        headers = {'Key': self.api_key, 'Sign': self._generate_signature(params)}
        
        try:
            response = self.session.post(self.TAPI_URL, data=params, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()
            return data.get('success') == 1
        except Exception as e:
            logger.error(f"❌ Gagal transfer: {e}")
            return False