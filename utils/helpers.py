import os
import json
import requests
import logging
from datetime import datetime
from config.settings import (
    MIN_PROFIT_THRESHOLD_USD,
    MIN_PROFIT_THRESHOLD_PERCENT,
    TRANSFER_FEE,
    TRANSFER_FEE_IDR_TO_USDT,
    MIN_TRADE_AMOUNTS
)

# Dapatkan logger
logger = logging.getLogger(__name__)

# Fungsi untuk mendapatkan kurs USD/IDR
def get_usd_to_idr_rate():
    if os.getenv("USD_TO_IDR_RATE"):
        try:
            return float(os.getenv("USD_TO_IDR_RATE"))
        except ValueError:
            logger.warning("⚠️ Format USD_TO_IDR_RATE tidak valid")
    
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest?from=USD&to=IDR", 
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data["rates"]["IDR"]
    except Exception as e:
        logger.warning(f"⚠️ Gagal ambil kurs dari API: {e}")
    
    return float(os.getenv("FALLBACK_USD_TO_IDR_RATE", "15000"))

def save_last_usd_to_idr_rate(rate):
    """Simpan kurs terakhir ke file"""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/last_rate.json", "w") as f:
            json.dump({
                "usd_to_idr": rate,
                "timestamp": datetime.now().isoformat()
            }, f)
    except Exception as e:
        logger.error(f"🚨 Gagal simpan kurs: {e}")

def load_last_usd_to_idr_rate():
    """Muat kurs dari file lokal"""
    try:
        if os.path.exists("data/last_rate.json"):
            with open("data/last_rate.json", "r") as f:
                data = json.load(f)
                return float(data["usd_to_idr"])
    except Exception as e:
        logger.error(f"🚨 Gagal muat kurs dari file: {e}")
    
    return float(os.getenv("FALLBACK_USD_TO_IDR_RATE", "15000"))

# Fungsi untuk mendapatkan setting
def get_setting(key, default=None):
    return os.getenv(key, default)

def get_min_profit_threshold():
    return (
        float(os.getenv("MIN_PROFIT_THRESHOLD_USD", "0.2")),
        float(os.getenv("MIN_PROFIT_THRESHOLD_PERCENT", "0.1"))
    )


def calculate_net_profit(symbol, buy_price, sell_price, buy_exchange, sell_exchange):
    coin_transfer_fee = TRANSFER_FEE.get(symbol, 0)
    fiat_transfer_fee = TRANSFER_FEE_IDR_TO_USDT if "indodax" in [buy_exchange, sell_exchange] else 0
    trade_fee = (buy_price * 0.001) + (sell_price * 0.001)
    
    total_fee = coin_transfer_fee + fiat_transfer_fee + trade_fee
    gross_profit = sell_price - buy_price
    net_profit = gross_profit - total_fee
    net_profit_percent = (net_profit / buy_price) * 100 if buy_price > 0 else 0
    
    return {
        'gross_profit': gross_profit,
        'total_fee': total_fee,
        'net_profit': net_profit,
        'net_profit_percent': net_profit_percent
    }

def calculate_trade_amount(symbol, buy_ex, sell_ex, buy_price, sell_price):
    buy_currency = buy_ex.get_base_currency()
    sell_currency = sell_ex.get_base_currency()
    
    buy_balance = buy_ex.fetch_balance().get(buy_currency, {}).get('free', 0)
    sell_balance = sell_ex.fetch_balance().get(symbol, {}).get('free', 0)
    
    max_from_buy = buy_balance / buy_price if buy_price > 0 else 0
    trade_amount = min(sell_balance, max_from_buy)
    min_amount = MIN_TRADE_AMOUNTS.get(symbol, 0.001)
    
    min_for_profit = get_required_amount_for_profit(symbol, buy_price, sell_price)
    
    return {
        'required_amount': trade_amount,
        'executable': trade_amount >= min_amount and trade_amount >= min_for_profit,
        'min_balance_required': max(min_amount, min_for_profit)
    }

def get_required_amount_for_profit(symbol, buy_price, sell_price):
    min_profit_usd, _ = get_min_profit_threshold()
    spread = sell_price - buy_price
    
    if spread <= 0:
        return float('inf')
    
    min_amount = min_profit_usd / spread
    return max(min_amount, MIN_TRADE_AMOUNTS.get(symbol, 0.001))

def get_active_exchanges():
    active_exchanges = os.getenv("ACTIVE_EXCHANGES", "Binance,Indodax,KuCoin").split(",")
    exchanges = []
    
    for name in active_exchanges:
        name = name.strip().lower()
        try:
            if name == "binance":
                from exchanges.binance import Binance
                ex = Binance()
                logger.info(f"✅ {name.capitalize()} initialized")
                exchanges.append(ex)
                
            elif name == "indodax":
                from exchanges.indodax import Indodax
                ex = Indodax()
                logger.info(f"✅ {name.capitalize()} initialized")
                exchanges.append(ex)
                
            elif name == "kucoin":
                from exchanges.kucoin import KuCoin
                ex = KuCoin()
                logger.info(f"✅ {name.capitalize()} initialized")
                exchanges.append(ex)
                
        except Exception as e:
            logger.error(f"❌ Gagal inisialisasi exchange {name}: {str(e)}")
    
    return exchanges

def get_wallet_address(exchange, symbol):
    exchange_name = exchange.__class__.__name__.upper()
    symbol_name = symbol.upper()
    wallet_env_key = f"{exchange_name}_{symbol_name}_WALLET"
    wallet_info = os.getenv(wallet_env_key)

    if not wallet_info:
        logger.warning(f"⚠️ Alamat wallet tidak ditemukan untuk {symbol_name} di {exchange_name}")
        return {'address': None, 'network': None, 'destination_tag': None}

    parts = wallet_info.split(':')
    result = {'address': parts[0]}
    
    if len(parts) > 1:
        result['destination_tag'] = parts[1]
    if len(parts) > 2:
        result['network'] = parts[2]
    
    return result

def get_exchange_class(exchange_name):
    """Dapatkan class exchange berdasarkan nama (case-insensitive)"""
    exchange_map = {
        "binance": "Binance",
        "indodax": "Indodax",
        "kucoin": "KuCoin",
        "bybit": "Bybit",
        "poloniex": "Poloniex"
    }
    
    normalized_name = exchange_name.strip().lower()
    return exchange_map.get(normalized_name, exchange_name.capitalize())