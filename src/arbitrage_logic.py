# src/arbitrage_logic.py
import asyncio
import websockets
import json
import os
from exchanges.binance import Binance
from exchanges.indodax import Indodax
from utils.helpers import (
    calculate_net_profit,
    calculate_trade_amount,
    check_balance_on_exchange,
    get_usd_to_idr_rate
)
from config.settings import (
    MIN_PROFIT_THRESHOLD_USD,
    MIN_PROFIT_THRESHOLD_PERCENT
)
from utils.logger import logger

# Muat daftar koin dari .env
SUPPORTED_SYMBOLS = os.getenv('SUPPORTED_SYMBOLS', 'BTC,XRP,BNB').split(',')

# Inisialisasi harga terakhir
latest_prices = {
    'binance': {},
    'indodax': {}
}

# Inisialisasi exchange
binance_api = Binance()
indodax_api = Indodax()

async def listen_binance_websocket():
    """
    WebSocket untuk Binance dengan dukungan multi-coin
    Format: BTCUSDT@trade, XRPUSDT@trade, dll.
    """
    symbols = [f"{s}USDT" for s in SUPPORTED_SYMBOLS]
    streams = '/'.join([f"{s}@trade" for s in symbols])
    uri = f"wss://stream.binance.com:9443/ws/{streams}"

    while True:
        try:
            async with websockets.connect(uri, ping_interval=20, ping_timeout=20) as websocket:
                logger.info("🟢 WebSocket Binance terhubung untuk multi-coin")
                while True:
                    msg = await websocket.recv()
                    data = json.loads(msg)
                    symbol = data['s'].replace('USDT', '')  # BTCUSDT → BTC
                    
                    if symbol in SUPPORTED_SYMBOLS:
                        latest_prices['binance'][symbol] = float(data['p'])
                        logger.debug(f"📈 Binance {symbol}/USDT: ${data['p']}")
        except Exception as e:
            logger.error(f"🔴 WebSocket Binance terputus: {e}. Reconnecting...")
            await asyncio.sleep(5)

def fetch_indodax_price():
    """
    Polling harga Indodax untuk semua simbol yang didukung
    Jika pasar tidak tersedia, log sebagai peringatan
    """
    for symbol in SUPPORTED_SYMBOLS:
        try:
            ticker = indodax_api.fetch_ticker(symbol)
            if ticker:
                latest_prices['indodax'][symbol] = ticker
                logger.debug(f"📉 Indodax {symbol}/IDR: Rp{ticker:,}")
            else:
                logger.warning(f"🚫 Pasangan {symbol}/IDR tidak ditemukan di Indodax")
                latest_prices['indodax'][symbol] = None
        except Exception as e:
            logger.error(f"🚨 Gagal ambil harga {symbol} dari Indodax: {e}")
            latest_prices['indodax'][symbol] = None

def check_arbitrage_opportunity():
    opportunities = []
    for symbol in SUPPORTED_SYMBOLS:
        price_binance = latest_prices['binance'].get(symbol)
        price_indodax = latest_prices['indodax'].get(symbol)
        if not price_binance or not price_indodax:
            logger.warning(f"⏳ Tunggu harga {symbol} dari Binance dan Indodax...")
            continue
        
        usd_to_idr = get_usd_to_idr_rate()
        price_indodax_usd = price_indodax / usd_to_idr
        spread = abs(price_binance - price_indodax_usd)
        fee_total = (price_binance * 0.001) + (price_indodax_usd * 0.001)
        profit = spread - fee_total
        profit_percent = (profit / price_binance) * 100 if price_binance > 0 else 0

        if profit > MIN_PROFIT_THRESHOLD_USD and profit_percent > MIN_PROFIT_THRESHOLD_PERCENT:
            opportunities.append({
                'symbol': symbol,
                'buy_exchange': 'Binance' if price_binance < price_indodax_usd else 'Indodax',
                'sell_exchange': 'Indodax' if price_binance < price_indodax_usd else 'Binance',
                'buy_price': round(min(price_binance, price_indodax_usd), 6),
                'sell_price': round(max(price_binance, price_indodax_usd), 6),
                'profit': round(profit, 6),
                'profit_percent': round(profit_percent, 2),
                'usd_to_idr': usd_to_idr,
                'amount': calculate_trade_amount(
                    symbol=symbol,
                    buy_exchange=Binance() if price_binance < price_indodax_usd else Indodax(),
                    sell_exchange=Indodax() if price_binance < price_indodax_usd else Binance(),
                    buy_price=min(price_binance, price_indodax_usd),
                    sell_price=max(price_binance, price_indodax_usd),
                    usd_to_idr=usd_to_idr
                ) or 0.001
            })
        else:
            logger.warning(f"📉 {symbol} tidak layak: Spread: ${profit:.6f} ({profit_percent:.2f}%) < Threshold")
    
    return opportunities

async def run_bot():
    """
    Fungsi utama bot arbitrase
    """
    logger.info("🚀 Bot arbitrase crypto dimulai...")
    usd_to_idr = get_usd_to_idr_rate()
    logger.info(f"💱 Kurs USD/IDR: {usd_to_idr}")

    # Jalankan WebSocket Binance di latar belakang
    asyncio.create_task(listen_binance_websocket())

    while True:
        try:
            # Perbarui harga Indodax
            fetch_indodax_price()
            
            # Cek peluang arbitrase
            opportunities = check_arbitrage_opportunity(usd_to_idr)
            
            # Eksekusi peluang arbitrase
            if opportunities:
                logger.info(f"✅ Menemukan {len(opportunities)} peluang arbitrase")
                for opportunity in opportunities:
                    logger.info(f"🚀 Mengeksekusi arbitrase {opportunity['symbol']}")
                    # Simulasi eksekusi
                    logger.info(f"📊 Hasil: Profit Bersih ${opportunity['net_profit']:.6f} ({opportunity['net_profit_percent']}%)")
            else:
                logger.info("🔍 Tidak ada peluang arbitrase saat ini")
                
        except Exception as e:
            logger.error(f"🚨 Kesalahan dalam siklus utama: {e}")
        
        # Tunggu sebelum cek ulang
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(run_bot())