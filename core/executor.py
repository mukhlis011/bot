# core/executor.py
from utils.helpers import calculate_net_profit
from config.settings import MIN_PROFIT_THRESHOLD_USD
from utils.logger import logger

class RealTradeExecutor:
    def __init__(self, *exchanges):
        self.exchanges = {ex.__class__.__name__.lower(): ex for ex in exchanges}

    def execute(self, opportunity):
        """
        Jalankan transaksi jika layak
        """
        symbol = opportunity.get('symbol')
        buy_exchange_name = opportunity.get('buy_exchange', '').lower()
        sell_exchange_name = opportunity.get('sell_exchange', '').lower()
        buy_price = opportunity.get('buy_price', 0)
        sell_price = opportunity.get('sell_price', 0)
        usd_to_idr = opportunity.get('usd_to_idr', 1.0)

        # Dapatkan instance exchange
        buy_exchange = self.exchanges.get(buy_exchange_name)
        sell_exchange = self.exchanges.get(sell_exchange_name)

        if not buy_exchange or not sell_exchange:
            logger.error("🚨 Exchange tidak ditemukan")
            return False

        # Dapatkan alamat wallet
        try:
            wallet_info = get_wallet_address(sell_exchange, symbol)
        except Exception as e:
            logger.warning(f"⚠️ Alamat wallet tidak ditemukan: {e}")
            return False

        # Dapatkan saldo aktual
        try:
            buy_balance_data = buy_exchange.fetch_balance()
            sell_balance_data = sell_exchange.fetch_balance()
        except Exception as e:
            logger.error(f"🚨 Gagal fetch balance: {e}")
            return False

        # Pastikan semua data tersedia
        buy_fiat_balance = 0
        buy_fiat_balance_usd = 0
        sell_balance = 0

        if buy_exchange.get_base_currency() in ['USDT', 'USD']:
            buy_fiat_balance = buy_balance_data.get('USDT', {}).get('free', 0) + buy_balance_data.get('USD', {}).get('free', 0)
            buy_fiat_balance_usd = buy_fiat_balance
        else:
            buy_fiat_balance = buy_balance_data.get('IDR', {}).get('free', 0)
            buy_fiat_balance_usd = buy_fiat_balance / usd_to_idr

        sell_balance = sell_balance_data.get(symbol, {}).get('free', 0)

        # Hitung jumlah maksimum yang bisa ditransfer
        max_by_fiat = buy_fiat_balance_usd / buy_price
        trade_amount = min(sell_balance, max_by_fiat)
        min_amount = MIN_TRADE_AMOUNTS.get(symbol, 0.001)
        required_amount = get_required_amount_for_profit(
            symbol=symbol,
            buy_price=buy_price,
            sell_price=sell_price,
            usd_to_idr=usd_to_idr
        )

        # Tampilkan log detail
        logger.info(f"""
        ┌────────────────────────────────────────────────────┐
        │ 📊 Rincian Peluang Arbitrase: {symbol}          │
        ├────────────────────────────────────────────────────┤
        │ Volume Minimum: {required_amount:.6f} {symbol}     │
        │ Saldo Penjual: {sell_balance:.6f} {symbol}        │
        │ Saldo Pembeli: {buy_fiat_balance:.6f} {buy_exchange.get_base_currency()} (≈${buy_fiat_balance_usd:.6f} USD) │
        └────────────────────────────────────────────────────┘
        """)

        # Cek apakah layak secara volume dan profit
        if trade_amount < min_amount:
            logger.warning(f"⚠️ Volume terlalu kecil untuk {symbol}. Minimum: {min_amount} {symbol}.")
            return False

        # Cek apakah ada cukup saldo
        if not check_balance_on_exchange(buy_exchange, symbol, trade_amount, buy_price):
            logger.warning(f"⚠️ Saldo tidak mencukupi untuk membeli {trade_amount} {symbol}")
            return False

        if not check_balance_on_exchange(sell_exchange, symbol, trade_amount, sell_price):
            logger.warning(f"⚠️ Saldo tidak mencukupi untuk menjual {trade_amount} {symbol}")
            return False

        # Eksekusi transfer koin
        try:
            logger.info(f"🔁 Memulai proses transfer {trade_amount} {symbol}...")
            success = buy_exchange.transfer_coin(
                symbol=symbol,
                amount=trade_amount,
                address=wallet_info['address'],
                tag=wallet_info.get('destination_tag'),
                network=wallet_info.get('network')
            )
            if success:
                logger.info(f"✅ Transfer {symbol} berhasil")
                return True
            else:
                logger.error(f"❌ Transfer {symbol} gagal")
                return False
        except Exception as e:
            logger.error(f"🚨 Gagal eksekusi transfer: {e}")
            return False