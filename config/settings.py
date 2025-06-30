import os
from dotenv import load_dotenv

load_dotenv()

# Mode bot
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "False") == "True"
NO_TRADE_MODE = os.getenv("NO_TRADE_MODE", "False") == "True"

# Threshold Profit
MIN_PROFIT_THRESHOLD_USD = float(os.getenv("MIN_PROFIT_THRESHOLD_USD", "0.2"))
MIN_PROFIT_THRESHOLD_PERCENT = float(os.getenv("MIN_PROFIT_THRESHOLD_PERCENT", "0.1"))

# Biaya Transfer
TRANSFER_FEE = {
    'BTC': float(os.getenv("TRANSFER_FEE_BTC", "0.000002")),
    'XRP': float(os.getenv("TRANSFER_FEE_XRP", "0.1")),
    'SHIB': float(os.getenv("TRANSFER_FEE_SHIB", "1000000")),
    'BNB': float(os.getenv("TRANSFER_FEE_BNB", "0.001"))
}

# Biaya Transfer Fiat
TRANSFER_FEE_IDR_TO_USDT = float(os.getenv("TRANSFER_FEE_IDR_TO_USDT", "10000"))

# Minimum trade amount
MIN_TRADE_AMOUNTS = {
    'BTC': float(os.getenv("MIN_TRADE_BTC", "0.00001")),
    'ETH': float(os.getenv("MIN_TRADE_ETH", "0.0001")),
    'BNB': float(os.getenv("MIN_TRADE_BNB", "0.001")),
    'XRP': float(os.getenv("MIN_TRADE_XRP", "1")),
    'SHIB': float(os.getenv("MIN_TRADE_SHIB", "1000000"))
}

SUPPORTED_SYMBOLS = os.getenv('SUPPORTED_SYMBOLS', 'BTC,XRP,SHIB,BNB').split(',')
ACTIVE_EXCHANGES = os.getenv('ACTIVE_EXCHANGES', 'Binance,Indodax,KuCoin').split(',')