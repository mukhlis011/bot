from utils.helpers import calculate_net_profit, calculate_trade_amount, convert_to_usd, get_required_amount_for_profit
from config.settings import MIN_PROFIT_THRESHOLD_PERCENT, MIN_PROFIT_THRESHOLD_USD
from utils.logger import logger
from tabulate import tabulate
import math

def check_transfer_opportunity(prices, usd_to_idr, *exchanges):
    """
    Cek peluang arbitrase antar exchange
    Args:
        prices: Dict harga dari semua exchange
        usd_to_idr: Kurs USD ke IDR
        *exchanges: Daftar exchange aktif (Binance, Indodax, KuCoin)
    Returns:
        list: Daftar peluang arbitrase
    """
    opportunities = []
    
    for symbol in prices.get('binance', {}).keys():
        price_data = {}
        
        # Kumpulkan harga dari semua exchange
        for ex in exchanges:
            ex_name = ex.__class__.__name__.lower()
            raw_price = prices[ex_name].get(symbol)
            
            if raw_price <= 0:
                logger.warning(f"⚠️ Harga {symbol} di {ex_name} tidak valid: {raw_price}")
                continue
            
            base_currency = ex.get_base_currency()  # ✅ Dipanggil pada instance exchange
            # Konversi IDR ke USD jika diperlukan
            if base_currency == "IDR":
                converted_price = raw_price / usd_to_idr
                price_data[ex_name] = {
                    'price': converted_price,
                    'currency': base_currency,
                    'raw_price': raw_price
                }
            else:
                price_data[ex_name] = {
                    'price': raw_price,
                    'currency': base_currency,
                    'raw_price': raw_price
                }
        
        # Pastikan ada setidaknya 2 exchange dengan harga valid
        if len(price_data) >= 2:
            # Urutkan berdasarkan harga
            sorted_prices = sorted(price_data.items(), key=lambda x: x[1]['price'])
            buy_ex_name, buy_data = sorted_prices[0]
            sell_ex_name, sell_data = sorted_prices[-1]
            
            # Dapatkan instance exchange
            buy_exchange = next(ex for ex in exchanges if ex.__class__.__name__.lower() == buy_ex_name.lower())
            sell_exchange = next(ex for ex in exchanges if ex.__class__.__name__.lower() == sell_ex_name.lower())
            
            # Hitung jumlah koin minimum
            trade_details = calculate_trade_amount(
                symbol=symbol,
                buy_exchange=buy_exchange,
                sell_exchange=sell_exchange,
                buy_price=buy_data['price'],
                sell_price=sell_data['price'],
                usd_to_idr=usd_to_idr
            ) or {}
            
            # Buat opportunity
            opportunity = {
                'symbol': symbol,
                'price_data': price_data,
                'usd_to_idr': usd_to_idr,
                'required_amount': trade_details.get('required_amount', 0),
                'sell_balance': trade_details.get('sell_balance', 0),
                'buy_fiat_balance': trade_details.get('buy_fiat_balance', 0)
            }
            opportunity.update(calculate_net_profit(opportunity))
            opportunities.append(opportunity)
    
    return opportunities