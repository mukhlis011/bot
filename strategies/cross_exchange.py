from utils.helpers import (
    calculate_net_profit,
    calculate_trade_amount,
    get_min_profit_threshold
)
from utils.logger import logger
from config.settings import SUPPORTED_SYMBOLS

def find_arbitrage_opportunities(prices, exchanges):
    opportunities = []
    min_profit_usd, min_profit_percent = get_min_profit_threshold()
    
    for symbol in SUPPORTED_SYMBOLS:
        # Cari exchange dengan harga terendah dan tertinggi
        buy_exchange = None
        sell_exchange = None
        lowest_price = float('inf')
        highest_price = 0
        
        for ex_name, symbol_prices in prices.items():
            price = symbol_prices.get(symbol, 0)
            if price > 0:  # Hanya pertimbangkan harga valid
                if price > highest_price:
                    highest_price = price
                    sell_exchange = ex_name
                if price < lowest_price:
                    lowest_price = price
                    buy_exchange = ex_name
        
        # Periksa apakah ada peluang arbitrase
        if buy_exchange and sell_exchange and buy_exchange != sell_exchange:
            spread = highest_price - lowest_price
            profit_data = calculate_net_profit(
                symbol,
                lowest_price,
                highest_price,
                buy_exchange,
                sell_exchange
            )
            
            # Dapatkan instance exchange
            buy_ex = next(ex for ex in exchanges if ex.__class__.__name__.lower() == buy_exchange)
            sell_ex = next(ex for ex in exchanges if ex.__class__.__name__.lower() == sell_exchange)
            
            # Hitung jumlah yang bisa ditradingkan
            trade_details = calculate_trade_amount(
                symbol, 
                buy_ex, 
                sell_ex, 
                lowest_price, 
                highest_price
            )
            
            # Periksa apakah profit memenuhi threshold
            if profit_data['net_profit'] > min_profit_usd and profit_data['net_profit_percent'] > min_profit_percent:
                opportunity = {
                    'symbol': symbol,
                    'buy_exchange': buy_exchange,
                    'sell_exchange': sell_exchange,
                    'buy_price': lowest_price,
                    'sell_price': highest_price,
                    'spread': spread,
                    'net_profit': profit_data['net_profit'],
                    'net_profit_percent': profit_data['net_profit_percent'],
                    'required_amount': trade_details['required_amount'],
                    'executable': trade_details['executable'],
                    'min_balance_required': trade_details['min_balance_required']
                }
                
                # Format log
                log_opportunity(opportunity)
                opportunities.append(opportunity)
    
    return opportunities

def log_opportunity(opp):
    status = "✅ LAYAK" if opp['executable'] else f"⚠️ SALDO MINIMAL: {opp['min_balance_required']:.6f} {opp['symbol']}"
    
    logger.info(f"""
    ┌────────────────────────────────────────────────────┐
    │ 🔍 ARBITRAGE OPPORTUNITY: {opp['symbol']}
    ├────────────────────────────────────────────────────┤
    │ Beli di: {opp['buy_exchange'].upper():<10} Harga: ${opp['buy_price']:.6f}
    │ Jual di: {opp['sell_exchange'].upper():<9} Harga: ${opp['sell_price']:.6f}
    ├────────────────────────────────────────────────────┤
    │ Spread: ${opp['spread']:.6f} 
    │ Profit: ${opp['net_profit']:.6f} ({opp['net_profit_percent']:.2f}%)
    │ Jumlah: {opp['required_amount']:.6f} {opp['symbol']}
    ├────────────────────────────────────────────────────┤
    │ Status: {status}
    └────────────────────────────────────────────────────┘
    """)