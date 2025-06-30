import asyncio
import os
import logging
import time
import ntplib
from dotenv import load_dotenv

load_dotenv()

from utils.helpers import get_active_exchanges
from utils.logger import setup_logger
from core.price_collector import PriceCollector
from core.arbitrage_engine import ArbitrageEngine
from core.transfer_manager import TransferManager
from strategies.balance_rotator import BalanceRotator

# Setup logger
logger = setup_logger()
logger.setLevel(logging.DEBUG)  # Set ke DEBUG untuk lebih banyak log

def sync_system_time():
    try:
        client = ntplib.NTPClient()
        response = client.request('pool.ntp.org')
        current_time = time.time()
        ntp_time = response.tx_time
        time_diff = abs(ntp_time - current_time)
        
        if time_diff > 30:  # Jika selisih waktu lebih dari 30 detik
            logger.warning(f"⚠️ Waktu sistem tidak sinkron! Selisih: {time_diff:.2f} detik")
            logger.warning("Harap sinkronkan waktu sistem Anda")
        else:
            logger.info(f"✅ Waktu sistem sinkron (selisih: {time_diff:.2f} detik)")
    except Exception as e:
        logger.error(f"❌ Gagal sinkronisasi waktu: {e}")

async def run_bot():
    logger.info("🚀 Memulai bot arbitrase crypto...")
    os.makedirs("data/logs", exist_ok=True)
    
    # Sinkronisasi waktu sistem
    sync_system_time()
    
    try:
        # Muat exchange aktif
        exchanges = get_active_exchanges()
        exchange_names = [ex.__class__.__name__ for ex in exchanges]
        logger.info(f"💱 Exchange aktif: {', '.join(exchange_names)}")
        
        # Beri waktu untuk inisialisasi
        await asyncio.sleep(2)
        
        # Inisialisasi komponen
        price_collector = PriceCollector(exchanges)
        arbitrage_engine = ArbitrageEngine(price_collector, exchanges)
        transfer_manager = TransferManager(exchanges)
        balance_rotator = BalanceRotator(exchanges)
        
        while True:
            try:
                # 1. Putar saldo ke posisi optimal
                await balance_rotator.rotate_balances()
                
                # 2. Jalankan deteksi arbitrase
                logger.debug("🔄 Mengumpulkan harga dari exchange...")
                opportunities = arbitrage_engine.run()
                
                if opportunities:
                    logger.info(f"✅ Ditemukan {len(opportunities)} peluang arbitrase")
                    
                    # 3. Eksekusi peluang
                    for opportunity in opportunities:
                        logger.info(f"🚀 Mengeksekusi peluang: {opportunity['symbol']}")
                        success = await transfer_manager.execute_arbitrage(opportunity)
                        
                        if success:
                            logger.info(f"✅ Arbitrase berhasil: {opportunity['symbol']}")
                        else:
                            logger.warning(f"⚠️ Gagal eksekusi arbitrase: {opportunity['symbol']}")
                else:
                    logger.info("🔍 Tidak ada peluang arbitrase saat ini")
                
                # 4. Tunggu sebelum iterasi berikutnya
                await asyncio.sleep(60)
                    
            except Exception as e:
                logger.error(f"🚨 Kesalahan dalam siklus utama: {e}")
                await asyncio.sleep(10)
                
    except Exception as e:
        logger.critical(f"🛑 Bot gagal diinisialisasi: {e}")

if __name__ == "__main__":
    asyncio.run(run_bot())