import os
import hmac
import base64
import hashlib
import time
import requests
import json
import logging
from .exchange_interface import Exchange

logger = logging.getLogger(__name__)

class KuCoin(Exchange):
    BASE_URL = "https://api.kucoin.com"
    
    def __init__(self):
        self.api_key = os.getenv("KUCOIN_API_KEY")
        self.api_secret = os.getenv("KUCOIN_API_SECRET")
        self.api_passphrase = os.getenv("KUCOIN_API_PASSPHRASE")
        if not all([self.api_key, self.api_secret, self.api_passphrase]):
            raise ValueError("KuCoin API key, secret, dan passphrase wajib di-set")
        self.session = requests.Session()
        logger.info("✅ KuCoin client initialized successfully")

    def get_base_currency(self):
        return "USDT"

    def _generate_signature(self, endpoint, method, params=None, body=None):
        now = str(int(time.time() * 1000))
        str_to_sign = now + method.upper() + endpoint
        
        # Handle query parameters
        if params:
            sorted_params = sorted(params.items())
            query_string = "&".join([f"{k}={v}" for k, v in sorted_params])
            str_to_sign += f"?{query_string}"
        
        # Handle request body
        if body:
            str_to_sign += json.dumps(body, separators=(',', ':'), ensure_ascii=False)
        
        logger.debug(f"String to sign: {str_to_sign}")
        
        # Create signature
        signature = base64.b64encode(
            hmac.new(
                self.api_secret.encode('utf-8'),
                str_to_sign.encode('utf-8'),
                hashlib.sha256
            ).digest()
        ).decode()
        
        # Passphrase should be base64 encoded
        passphrase = base64.b64encode(self.api_passphrase.encode('utf-8')).decode()
        
        return {
            "KC-API-KEY": self.api_key,
            "KC-API-SIGN": signature,
            "KC-API-TIMESTAMP": now,
            "KC-API-PASSPHRASE": passphrase,
            "KC-API-KEY-VERSION": "2",
            "Content-Type": "application/json"
        }

    def fetch_ticker(self, symbol):
        endpoint = "/api/v1/market/orderbook/level1"
        params = {"symbol": f"{symbol.upper().replace('_', '-')}"}
        headers = self._generate_signature(endpoint, "GET", params=params)

        try:
            response = self.session.get(
                f"{self.BASE_URL}{endpoint}", 
                params=params,
                headers=headers,
                timeout=10
            )
            logger.debug(f"KuCoin response: {response.status_code} {response.text}")

            if response.status_code == 401:
                logger.error("❌ Autentikasi KuCoin gagal. Periksa API Key, Secret, dan Passphrase")
                return 0.0

            response.raise_for_status()
            data = response.json()

            # Pastikan data valid dan struktur lengkap sebelum akses
            if data and data.get("code") == "200000" and "data" in data and data["data"]:
                price = data["data"].get("price")
                if price is not None:
                    return float(price)
                else:
                    logger.error(f"❌ Harga tidak ditemukan di respons KuCoin: {data}")
                    return 0.0
            else:
                logger.error(f"❌ Format respons tidak valid dari KuCoin: {data}")
                return 0.0

        except Exception as e:
            logger.error(f"❌ Gagal fetch ticker KuCoin {symbol}: {e}")
            return 0.0

    def fetch_balance(self):
        endpoint = "/api/v1/accounts"
        headers = self._generate_signature(endpoint, "GET")
        
        try:
            response = self.session.get(
                f"{self.BASE_URL}{endpoint}",
                headers=headers,
                timeout=10
            )
            
            # Debug logging
            logger.debug(f"KuCoin balance response: {response.status_code} {response.text}")
            
            if response.status_code == 401:
                logger.error("❌ Autentikasi KuCoin gagal. Periksa API Key, Secret, dan Passphrase")
                return {}
                
            response.raise_for_status()
            data = response.json()
            
            if data.get("code") == "200000":
                balances = {}
                for item in data["data"]:
                    if item["type"] == "trade":
                        currency = item["currency"]
                        free = float(item["available"])
                        balances[currency] = {"free": free}
                return balances
            else:
                logger.error(f"❌ Gagal fetch balance KuCoin: {data.get('msg')}")
                return {}
        except Exception as e:
            logger.error(f"❌ Error fetch balance KuCoin: {e}")
            return {}

    def transfer_coin(self, symbol, amount, address, tag=None, network=None):
        endpoint = "/api/v2/withdrawals"
        body = {
            "currency": symbol.upper(),
            "address": address,
            "amount": amount,
            "chain": network or self._get_network(symbol)
        }
        if tag:
            body["memo"] = tag
            
        headers = self._generate_signature(endpoint, "POST", body=body)
        try:
            response = self.session.post(
                f"{self.BASE_URL}{endpoint}", 
                json=body, 
                headers=headers, 
                timeout=20
            )
            
            # Debug logging
            logger.debug(f"KuCoin withdrawal response: {response.status_code} {response.text}")
            
            response.raise_for_status()
            data = response.json()
            if data.get("code") == "200000":
                logger.info(f"✅ Withdrawal KuCoin {amount} {symbol.upper()} to {address} sukses")
                return True
            else:
                logger.error(f"❌ Withdrawal KuCoin gagal: {data}")
                return False
        except Exception as e:
            logger.error(f"❌ Withdrawal KuCoin error: {e}")
            return False

    def _get_network(self, symbol):
        networks = {
            "BTC": "BTC",
            "ETH": "ERC20",
            "BNB": "BEP20",
            "XRP": "XRP",
            "USDT": "ERC20",
            "SHIB": "ERC20"
        }
        return networks.get(symbol, "ERC20")