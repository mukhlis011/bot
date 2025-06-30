from utils.helpers import (
    calculate_net_profit,
    calculate_trade_amount,
    get_min_profit_threshold
)
from utils.logger import logger
from config.settings import SUPPORTED_SYMBOLS
from colorama import init, Fore, Style

init(autoreset=True)

def find_arbitrage_opportunities(prices, exchanges):
    opportunities = []
    min_profit_usd, min_profit_percent = get_min_profit_threshold()
    
    logger.info(f"🧪 Threshold profit: ${min_profit_usd} atau {min_profit_percent*100:.2f}%")

    for symbol in SUPPORTED_SYMBOLS:
        # Cari exchange dengan harga terendah dan tertinggi
        buy_exchange = None
        sell_exchange = None
        lowest_price = float('inf')
        highest_price = 0
        
        for ex_name, symbol_prices in prices.items():
            price = symbol_prices.get(symbol, 0)
            if price > 0:
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

            # Ambil saldo untuk log
            buy_bal = buy_ex.fetch_balance()
            sell_bal = sell_ex.fetch_balance()
            buy_symbol_balance = buy_bal.get(symbol, {}).get('free', 0)
            buy_usdt_balance = buy_bal.get(buy_ex.get_base_currency(), {}).get('free', 0)
            sell_symbol_balance = sell_bal.get(symbol, {}).get('free', 0)
            sell_usdt_balance = sell_bal.get(sell_ex.get_base_currency(), {}).get('free', 0)

            # Simpan semua info peluang
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
                'min_balance_required': trade_details['min_balance_required'],
                'buy_symbol_balance': buy_symbol_balance,
                'buy_usdt_balance': buy_usdt_balance,
                'sell_symbol_balance': sell_symbol_balance,
                'sell_usdt_balance': sell_usdt_balance,
            }

            log_opportunity(opportunity)
            opportunities.append(opportunity)

    return opportunities

def log_opportunity(opp):
    status_color = Fore.GREEN if opp['executable'] else Fore.YELLOW
    status_text = "✅ LAYAK" if opp['executable'] else "⚠️ TIDAK LAYAK"
    reset = Style.RESET_ALL

    buy_ex = opp['buy_exchange'].upper()
    sell_ex = opp['sell_exchange'].upper()
    symbol = opp['symbol']

    logger.info(f"{Fore.CYAN}{'='*60}{reset}")
    logger.info(f"{Fore.MAGENTA}💹 ARBITRASE: {symbol}{reset}")
    logger.info(f"{Fore.BLUE}➤ BELI: {buy_ex} @ ${opp['buy_price']:.6f}{reset}")
    logger.info(f"{Fore.RED}➤ JUAL: {sell_ex} @ ${opp['sell_price']:.6f}{reset}")
    logger.info(f"{Fore.WHITE}➤ SPREAD: ${opp['spread']:.6f}{reset}")
    logger.info(f"{Fore.WHITE}➤ PROFIT: ${opp['net_profit']:.2f} ({opp['net_profit_percent']:.2f}%){reset}")
    logger.info(f"{Fore.YELLOW}➤ JUMLAH: {opp['required_amount']:.6f} {symbol} | MIN SALDO: ${opp['min_balance_required']:.2f}{reset}")
    logger.info(f"{status_color}➤ STATUS: {status_text} (min profit: ${opp['min_balance_required']:.2f}){reset}")
    logger.info(
        f"{Fore.LIGHTWHITE_EX}➤ Saldo {symbol} {buy_ex}: {opp['buy_symbol_balance']:.6f} | {buy_ex} {buy_ex_BASE(opp)}: {opp['buy_usdt_balance']:.2f}{reset}"
    )
    logger.info(
        f"{Fore.LIGHTWHITE_EX}➤ Saldo {symbol} {sell_ex}: {opp['sell_symbol_balance']:.6f} | {sell_ex} {sell_ex_BASE(opp)}: {opp['sell_usdt_balance']:.2f}{reset}"
    )
    logger.info(f"{Fore.CYAN}{'='*60}{reset}")

def buy_ex_BASE(opp):
    return "USDT" if opp['buy_exchange'] != "indodax" else "IDR"

def sell_ex_BASE(opp):
    return "USDT" if opp['sell_exchange'] != "indodax" else "IDR"
