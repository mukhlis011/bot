import os
import time
import hmac
import hashlib
import base64
import requests
from utils.logger import logger
from .exchange_interface import Exchange

class Poloniex(Exchange):
    BASE_URL = "https://api.poloniex.com"

    def __init__(self):
        self.api_key = os.getenv("POLONIEX_API_KEY")
        self.api_secret = os.getenv("POLONIEX_API_SECRET")

        if not self.api_key or not self.api_secret:
            raise ValueError("POLONIEX_API_KEY dan POLONIEX_API_SECRET wajib diatur di .env")

        self.session = requests.Session()
        logger.info("✅ Poloniex client initialized successfully")

    def get_base_currency(self) -> str:
        return "USDT"

    def fetch_ticker(self, symbol: str, usd_to_idr: float = 1.0) -> float:
        try:
            pair = f"{symbol.upper()}_USDT"
            url = f"{self.BASE_URL}/markets/{symbol.upper()}_USDT/price"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return float(data['price'])
        except Exception as e:
            logger.error(f"🚨 Gagal fetch ticker Poloniex {symbol}: {e}")
            return 0.0

    def fetch_balance(self) -> dict:
        try:
            timestamp = str(int(time.time() * 1000))
            method = "GET"
            endpoint = "/wallets/balances"

            signature = self._sign_request(method, endpoint, timestamp)

            headers = {
                "Poloniex-Key": self.api_key,
                "Poloniex-Timestamp": timestamp,
                "Poloniex-Signature": signature,
            }

            response = self.session.get(f"{self.BASE_URL}{endpoint}", headers=headers, timeout=10)
            response.raise_for_status()
            data = response.json()

            balances = {}
            for asset in data:
                currency = asset['currency']
                free = float(asset.get('available', 0))
                locked = float(asset.get('hold', 0))
                balances[currency] = {"free": free, "locked": locked}

            return balances
        except Exception as e:
            logger.error(f"🚨 Error fetch balance Poloniex: {e}")
            return {}

    def transfer_coin(self, symbol: str, amount: float, address: str, tag: str = None, network: str = None) -> bool:
        try:
            timestamp = str(int(time.time() * 1000))
            method = "POST"
            endpoint = "/wallets/withdraw"

            body = {
                "currency": symbol,
                "amount": str(amount),
                "address": address,
            }

            if tag:
                body["paymentId"] = tag

            signature = self._sign_request(method, endpoint, timestamp, body)

            headers = {
                "Poloniex-Key": self.api_key,
                "Poloniex-Timestamp": timestamp,
                "Poloniex-Signature": signature,
                "Content-Type": "application/json"
            }

            response = self.session.post(f"{self.BASE_URL}{endpoint}", json=body, headers=headers, timeout=20)
            response.raise_for_status()
            data = response.json()

            if data.get("withdrawalId"):
                logger.info(f"✅ Withdrawal Poloniex {amount} {symbol} ke {address} sukses")
                return True
            else:
                logger.error(f"🚨 Withdrawal Poloniex gagal: {data}")
                return False

        except Exception as e:
            logger.error(f"🚨 Error withdraw Poloniex: {e}")
            return False

    def _sign_request(self, method, endpoint, timestamp, body=None):
        path = endpoint
        body_str = ""

        if body:
            import json
            body_str = json.dumps(body, separators=(",", ":"))

        prehash = f"{timestamp}{method.upper()}{path}{body_str}"
        signature = hmac.new(
            self.api_secret.encode("utf-8"),
            prehash.encode("utf-8"),
            hashlib.sha512
        ).hexdigest()

        return signature

    def get_min_trade_amount(self, symbol: str) -> float:
        # Placeholder, bisa dihubungkan ke endpoint market info jika ada
        defaults = {
            "BTC": 0.0001,
            "XRP": 1,
            "SHIB": 100000,
            "BNB": 0.001
        }
        return defaults.get(symbol.upper(), 0.001)
