# strategies/auto_scanner.py
from utils.helpers import get_usd_to_idr_rate
from utils.logger import logger


def get_common_symbols(binance, indodax):
    """
    Cari koin yang tersedia di kedua exchange
    """
    try:
        binance_symbols = set(binance.get_supported_symbols())
        indodax_symbols = set(indodax.get_supported_symbols())
        common = binance_symbols.intersection(indodax_symbols)
        logger.info(f"🔍 Ditemukan {len(common)} simbol yang tersedia di kedua exchange")
        return sorted(common)
    except Exception as e:
        logger.error(f"🚨 Gagal mengambil simbol dari exchange: {e}")
        return []


def scan_spread_opportunities(binance, indodax, symbols):
    """
    Scan selisih harga terbesar antar exchange dari simbol yang sama
    """
    usd_to_idr = get_usd_to_idr_rate()
    opportunities = []

    for symbol in symbols:
        try:
            ticker_binance = binance.fetch_ticker(symbol)
            ticker_indodax = indodax.fetch_ticker(symbol)

            binance_price = ticker_binance.get("last")
            indodax_price_idr = ticker_indodax.get("last")

            if not binance_price or not indodax_price_idr:
                continue

            indodax_price_usd = indodax_price_idr / usd_to_idr
            spread = abs(binance_price - indodax_price_usd)
            spread_percent = (spread / binance_price) * 100 if binance_price else 0

            opportunities.append({
                "symbol": symbol,
                "binance_price": round(binance_price, 6),
                "indodax_price_idr": round(indodax_price_idr, 2),
                "indodax_price_usd": round(indodax_price_usd, 6),
                "spread": round(spread, 6),
                "spread_percent": round(spread_percent, 2),
            })
        except Exception as e:
            logger.warning(f"⚠️ Gagal ambil harga {symbol}: {e}")
            continue

    # Urutkan berdasarkan spread persentase terbesar
    opportunities.sort(key=lambda x: x['spread_percent'], reverse=True)
    return opportunities


def check_spread_opportunity(binance, indodax):
    """
    Fungsi utama strategi auto scanner untuk mendeteksi peluang spread besar
    """
    symbols = get_common_symbols(binance, indodax)
    if not symbols:
        logger.warning("⚠️ Tidak ada simbol yang sama di kedua exchange")
        return []

    opportunities = scan_spread_opportunities(binance, indodax, symbols)

    top_opps = opportunities[:5]  # Top 5 saja
    logger.info("\n📊 Top Spread Opportunities:")
    for opp in top_opps:
        logger.info(f"{opp['symbol']} | Spread {opp['spread_percent']}% | Binance ${opp['binance_price']} vs Indodax ${opp['indodax_price_usd']}")

    return opportunities