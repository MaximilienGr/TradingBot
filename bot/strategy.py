def strategy_testing(market_data):
    market_data.update_data()
    market_data.get_indicators_signals()
    market_data.protect_funds()
    if market_data.should_long():
        market_data.long()
    if market_data.should_short():
        market_data.short()
