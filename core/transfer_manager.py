from utils.helpers import get_wallet_address
from utils.logger import logger
from strategies.balance_rotator import BalanceRotator

class TransferManager:
    def __init__(self, exchanges):
        self.exchanges = {ex.__class__.__name__.lower(): ex for ex in exchanges}
        self.balance_rotator = BalanceRotator(exchanges)

    async def execute_arbitrage(self, opportunity):
        symbol = opportunity['symbol']
        buy_ex = self.exchanges[opportunity['buy_exchange']]
        sell_ex = self.exchanges[opportunity['sell_exchange']]
        amount = opportunity['required_amount']
        
        try:
            # 1. Putar saldo ke posisi yang diperlukan
            await self.balance_rotator.prepare_for_arbitrage(opportunity)
            
            # 2. Transfer koin ke exchange pembeli
            wallet_info = get_wallet_address(buy_ex, symbol)
            
            logger.info(f"🔁 Transfer {amount} {symbol} dari {sell_ex.__class__.__name__} ke {buy_ex.__class__.__name__}")
            success = sell_ex.transfer_coin(
                symbol,
                amount,
                wallet_info['address'],
                wallet_info.get('tag'),
                wallet_info.get('network')
            )
            
            if not success:
                logger.error("❌ Transfer gagal")
                return False
            
            # 3. Eksekusi arbitrase
            # (Implementasi eksekusi trading akan ditambahkan di sini)
            
            return True
        except Exception as e:
            logger.error(f"🚨 Error eksekusi arbitrase: {e}")
            return False