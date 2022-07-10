import time


def strategy_testing(
    market_data, market_data_history, open_position=False, sleep_time=0
):
    market_data.decide()
    if market_data.should_buy():
        buy_price = market_data.df.Close.iloc[-1]
        market_data.df.at[market_data.df.index[-1], "Bought"] = 1
        open_position = True
    while open_position and len(market_data_history) > 1:
        time.sleep(sleep_time)
        market_data.update_data()
        market_data.decide()
        if market_data.should_sell(buy_price=buy_price):
            # sell_price = market_data.df.Close.iloc[-1]
            market_data.df.at[market_data.df.index[-1], "Sell"] = 1
            break
