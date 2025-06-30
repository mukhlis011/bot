# core/transfer_executor.py
from utils.helpers import get_wallet_address, calculate_net_profit, convert_to_usd, get_usd_to_idr_rate
from config.settings import MIN_PROFIT_THRESHOLD_USD, MIN_PROFIT_THRESHOLD_PERCENT
from utils.logger import logger

class RealTradeExecutor:
    def __init__(self, *exchanges):
        self.exchanges = {ex.__class__.__name__.lower(): ex for ex in exchanges}
    
    def execute(self, opportunity):
        """
        Jalankan transaksi jika layak
        """
        symbol = opportunity['symbol']
        buy_exchange = self.exchanges[opportunity['buy_exchange'].lower()]
        sell_exchange = self.exchanges[opportunity['sell_exchange'].lower()]
        buy_price = opportunity['buy_price']
        sell_price = opportunity['sell_price']
        
        # Ambil alamat wallet
        wallet_info = get_wallet_address(buy_exchange, symbol)
        
        # Hitung profit
        profit_data = calculate_net_profit({
            'symbol': symbol,
            'buy_exchange': opportunity['buy_exchange'],
            'sell_exchange': opportunity['sell_exchange'],
            'buy_price': buy_price,
            'sell_price': sell_price,
            'usd_to_idr': opportunity['usd_to_idr']
        })
        
        # Tampilkan log detail meski tidak layak
        logger.info(f"""
        ┌────────────────────────────────────────────────────┐
        │ 📈 Peluang Arbitrase: {symbol}                  │
        ├────────────────────────────────────────────────────┤
        │ Pembelian: {profit_data['buy_exchange']}       │
        │ Harga Beli: ${profit_data['buy_price']:.6f}   │
        ├────────────────────────────────────────────────────┤
        │ Penjualan: {profit_data['sell_exchange']}      │
        │ Harga Jual: ${profit_data['sell_price']:.6f} │
        ├────────────────────────────────────────────────────┤
        │ Biaya Transaksi:                               │
        │   - Trading Buy: ${profit_data['fee_details']['trading_buy']:.6f}  │
        │   - Trading Sell: ${profit_data['fee_details']['trading_sell']:.6f}│
        │   - Transfer Koin: ${profit_data['fee_details']['coin_transfer']:.6f} │
        │   - Transfer Fiat: ${profit_data['fee_details']['fiat_transfer']:.6f} │
        ├────────────────────────────────────────────────────┤
        │ Profit Kotor: ${profit_data['gross_profit']:.6f} │
        │ Profit Bersih: ${profit_data['net_profit']:.6f}  │
        │ Persentase Profit: {profit_data['net_profit_percent']:.2f}% │
        │ Status: {"✅ Layak" if profit_data['is_executable'] else "❌ Tidak Layak"} │
        ├────────────────────────────────────────────────────┤
        │ Volume Minimum: {profit_data.get('required_amount', 0):.6f} {symbol} │
        │ Saldo Penjual: {opportunity.get('sell_balance', 0):.6f} {symbol} (≈${opportunity.get('sell_balance', 0) * sell_price:.6f}) │
        │ Saldo Pembeli: ${opportunity.get('buy_fiat_balance', 0):.6f} USD     │
        └────────────────────────────────────────────────────┘
        """)
        
        # Hanya eksekusi jika layak
        if profit_data['is_executable']:
            logger.info(f"✅ Transaksi {symbol} berhasil: Profit: ${profit_data['net_profit']:.6f}")
            return True
        else:
            logger.warning(f"❌ Transaksi {symbol} dilewatkan: Profit tidak memenuhi threshold")
            return False