# src/exchanges.py
import ccxt
import os
from dotenv import load_dotenv

# Muat variabel lingkungan dari .env
load_dotenv()

# Daftar koin yang didukung (dari .env)
SUPPORTED_SYMBOLS = os.getenv('SUPPORTED_SYMBOLS', 'BTC,ETH,XRP,SHIB,BNB').split(',')
logger = None  # Akan diinisialisasi dari setup_logger()

def setup_logger():
    """Setup logger dasar untuk modul ini"""
    import logging
    logging.basicConfig(
        format="[%(levelname)s] %(message)s",
        level=logging.INFO
    )
    return logging.getLogger(__name__)

def validate_api_keys(exchange_name):
    """Validasi API key tersedia di .env"""
    api_key = os.getenv(f"{exchange_name}_API_KEY")
    secret_key = os.getenv(f"{exchange_name}_SECRET_KEY")
    
    if not api_key or not secret_key:
        raise ValueError(f"🚫 {exchange_name} API key atau secret key tidak ditemukan di .env")
    
    return api_key, secret_key

def configure_binance():
    """Konfigurasi exchange Binance"""
    try:
        api_key, secret_key = validate_api_keys("BINANCE")
        
        binance = ccxt.binance({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True,
            'options': {
                'defaultType': 'spot',
                'fetchCurrenciesFromEndpoint': False,
                'fetchMarketsFromEndpoint': False,
            },
            'urls': {
                'api': {
                    'public': 'https://api.binance.com/api/v3 ',
                    'private': 'https://api.binance.com/api/v3 '
                }
            }
        })
        binance.load_markets()
        return binance
    except Exception as e:
        logger.error(f"🚨 Gagal konfigurasi Binance: {e}")
        raise

def configure_indodax():
    """Konfigurasi exchange Indodax"""
    try:
        api_key, secret_key = validate_api_keys("INDODAX")
        
        indodax = ccxt.indodax({
            'apiKey': api_key,
            'secret': secret_key,
            'enableRateLimit': True
        })
        indodax.load_markets()
        return indodax
    except Exception as e:
        logger.error(f"🚨 Gagal konfigurasi Indodax: {e}")
        raise

def get_exchange_instance(exchange_name):
    """Fungsi factory untuk mendapatkan instance exchange berdasarkan nama"""
    if exchange_name == 'Binance':
        return configure_binance()
    elif exchange_name == 'Indodax':
        return configure_indodax()
    else:
        raise ValueError(f"⚠️ Exchange '{exchange_name}' tidak didukung")

# Inisialisasi logger
logger = setup_logger()

# Inisialisasi exchange
try:
    # Konfigurasi Binance
    binance = configure_binance()
    
    # Konfigurasi Indodax
    indodax = configure_indodax()
    
    logger.info(f"✅ Exchange berhasil dikonfigurasi untuk: {', '.join(SUPPORTED_SYMBOLS)}")
except Exception as e:
    logger.critical(f"🛑 Bot gagal diinisialisasi: {e}")
    raise