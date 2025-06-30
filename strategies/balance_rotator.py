from utils.logger import logger

class BalanceRotator:
    def __init__(self, exchanges):
        self.exchanges = {ex.__class__.__name__.lower(): ex for ex in exchanges}
    
    async def rotate_balances(self):
        """Putar saldo ke exchange dengan yield terbaik"""
        # Implementasi logika rotasi otomatis
        # (Contoh: Pindahkan aset idle ke exchange dengan staking yield tertinggi)
        pass
    
    async def prepare_for_arbitrage(self, opportunity):
        """Siapkan saldo untuk peluang arbitrase"""
        symbol = opportunity['symbol']
        buy_ex_name = opportunity['buy_exchange']
        sell_ex_name = opportunity['sell_exchange']
        amount = opportunity['required_amount']
        
        # Periksa saldo di exchange penjual
        sell_ex = self.exchanges[sell_ex_name]
        sell_balance = sell_ex.fetch_balance().get(symbol, {}).get('free', 0)
        
        if sell_balance < amount:
            logger.warning(f"⚠️ Saldo {symbol} tidak cukup di {sell_ex_name}")
            await self.transfer_to_exchange(symbol, amount - sell_balance, sell_ex_name)
    
    async def transfer_to_exchange(self, symbol, amount, target_exchange):
        """Transfer koin ke exchange target dari exchange lain"""
        logger.info(f"🔄 Memindahkan {amount} {symbol} ke {target_exchange}")
        
        # 1. Cari exchange dengan saldo cukup
        for ex_name, exchange in self.exchanges.items():
            if ex_name == target_exchange:
                continue
                
            balance = exchange.fetch_balance().get(symbol, {}).get('free', 0)
            if balance >= amount:
                # 2. Transfer ke exchange target
                wallet_info = get_wallet_address(self.exchanges[target_exchange], symbol)
                success = exchange.transfer_coin(
                    symbol,
                    amount,
                    wallet_info['address'],
                    wallet_info.get('tag'),
                    wallet_info.get('network')
                )
                
                if success:
                    logger.info(f"✅ Berhasil transfer {amount} {symbol} dari {ex_name} ke {target_exchange}")
                    return True
        
        logger.error(f"❌ Tidak ada saldo {symbol} yang cukup di exchange lain")
        return False