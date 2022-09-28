def strategy_testing(market_data):
    market_data.update_data()
    market_data.get_indicators_signals()
    if market_data.should_quit():
        market_data.quit_position()
    if market_data.should_long():
        market_data.long()
    elif market_data.should_short():
        market_data.short()
