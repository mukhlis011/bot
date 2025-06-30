import asyncio
import os
import logging
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

async def run_bot():
    logger.info("🚀 Memulai bot arbitrase crypto...")
    os.makedirs("data/logs", exist_ok=True)
    
    try:
        # Muat exchange aktif
        exchanges = get_active_exchanges()
        exchange_names = [ex.__class__.__name__ for ex in exchanges]
        logger.info(f"💱 Exchange aktif: {', '.join(exchange_names)}")
        
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
                opportunities = arbitrage_engine.run()
                
                if opportunities:
                    logger.info(f"✅ Ditemukan {len(opportunities)} peluang arbitrase")
                    
                    # 3. Eksekusi peluang
                    for opportunity in opportunities:
                        if opportunity['executable']:
                            logger.info(f"🚀 Mengeksekusi peluang: {opportunity['symbol']}")
                            success = await transfer_manager.execute_arbitrage(opportunity)
                            
                            if success:
                                logger.info(f"✅ Arbitrase berhasil: {opportunity['symbol']}")
                            else:
                                logger.warning(f"⚠️ Gagal eksekusi arbitrase: {opportunity['symbol']}")
                        else:
                            logger.warning(f"⏳ Peluang tidak eksekusi: {opportunity['symbol']} (Saldo tidak cukup)")
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