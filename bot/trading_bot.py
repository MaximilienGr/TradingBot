import logging
import os
from binance.client import Client
from IPython.display import clear_output

from display import show_candlestick_with_plotly
from marketdata import MarketData
from mock.mock_client import MockClient
from profitability import get_impact
from strategy import strategy_testing
from utils import date_to_mili_timestamp

if __name__ == "__main__":
    logging.info("Let's start dat shit")

    binance_api_key = os.environ["BINANCE_API_KEY"]
    binance_secret_key = os.environ["BINANCE_SECRET_KEY"]
    client = Client(binance_api_key, binance_secret_key)
    # Which pair you want to trade
    symbol = "BTCUSDT"
    # Nombre de fenetre de retard toléré pour trigger un buy selon l'indicateur stochastique
    lags = 3

    stop_limit_percentage = 0.999
    stop_loss_percentage = 1.005
    rsi_window = 14
    rsi_trigger = 30
    macd_window_slow = 26
    macd_window_fast = 12
    macd_window_sign = 9
    stoch_window = 14
    stoch_smooth_window = 3
    stoch_trigger = 20
    stoch_limits = [20, 80]

    # # Candle size
    # interval = Client.KLINE_INTERVAL_1WEEK
    # simu_market_start_timestamp = date_to_mili_timestamp('01.01.2020 02:00:00')
    # # Attention, il faut au moins 33 itérations entre le début et la fin pour MACD ()
    # simu_market_stop_timestamp = date_to_mili_timestamp('04.09.2020 02:00:00')

    # history_start_timestamp = date_to_mili_timestamp('07.09.2020 02:00:00')
    # history_stop_timestamp = date_to_mili_timestamp('20.06.2022 02:00:00')

    # Candle size
    interval = Client.KLINE_INTERVAL_1MINUTE
    simu_market_start_timestamp = date_to_mili_timestamp("19.06.2022 02:00:00")
    # Attention, il faut au moins 33 itérations entre le début et la fin pour MACD ()
    simu_market_stop_timestamp = date_to_mili_timestamp("19.06.2022 04:00:00")

    # history_start_timestamp doit commencer 1 interval après la fin du simu_market
    history_start_timestamp = date_to_mili_timestamp("19.06.2022 04:01:00")
    history_stop_timestamp = date_to_mili_timestamp("19.06.2022 05:00:00")

    market_data_history = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=history_start_timestamp,
        end_str=history_stop_timestamp,
    )

    simu_market_data = MarketData(
        symbol=symbol,
        interval=interval,
        lags=lags,
        start_str=simu_market_start_timestamp,
        end_str=simu_market_stop_timestamp,
        client=client,
        stop_limit_percentage=stop_limit_percentage,
        stop_loss_percentage=stop_loss_percentage,
        rsi_trigger=rsi_trigger,
        rsi_window=rsi_window,
        macd_window_slow=macd_window_slow,
        macd_window_fast=macd_window_fast,
        macd_window_sign=macd_window_sign,
        stoch_window=stoch_window,
        stoch_smooth_window=stoch_smooth_window,
        stoch_trigger=stoch_trigger,
        stoch_limits=stoch_limits,
    )

    mock_client = MockClient(market_data_history=market_data_history)
    simu_market_data.client = mock_client

    while len(market_data_history) > 1:
        clear_output(wait=True)
        strategy_testing(
            market_data=simu_market_data,
            market_data_history=market_data_history,
            sleep_time=0,
        )
        simu_market_data.update_data()

    assert (simu_market_data.df.Bought.sum() - simu_market_data.df.Sell.sum()) in [0, 1]

    # show_candlestick(simu_market_data.df[-3:])
    impact = float("%.2f" % get_impact(simu_market_data.df))
    print(f"Impact: {impact} %")

    df = simu_market_data.df
    show_candlestick_with_plotly(df)
