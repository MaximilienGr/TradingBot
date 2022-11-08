from bot.tradingbot import TradingBot


def strategy_testing(trading_bot: TradingBot):
    trading_bot.update_data()
    trading_bot.get_indicators_signals()
    if trading_bot.should_quit():
        trading_bot.quit_position()
    if trading_bot.should_long():
        trading_bot.long()
    elif trading_bot.should_short():
        trading_bot.short()
