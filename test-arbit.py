from strategies.transfer_only import check_transfer_opportunity
opportunities = check_transfer_opportunity(Binance(), Indodax())
print("Opportunity Keys:", opportunities[0].keys())