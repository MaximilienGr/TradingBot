import logging
import os
from binance.client import Client
from IPython.display import clear_output

from marketdata import MarketData
from mock.mock_client import MockClient
from profitability import get_impact
from strategy import strategy_testing
from utils import date_to_mili_timestamp

from indicators.macd_indicator import MacdIndicator
from indicators.rsi_indicator import RsiIndicator
from indicators.stochastic_indicator import StochasticIndicator
from indicators.sma7_indicator import Sma7Indicator
from indicators.sma20_indicator import Sma20Indicator
from indicators.sma50_indicator import Sma50Indicator
from indicators.sma100_indicator import Sma100Indicator
from indicators.sma200_indicator import Sma200Indicator

if __name__ == "__main__":
    logging.info("Let's start dat shit")

    binance_api_key = os.environ["BINANCE_API_KEY"]
    binance_secret_key = os.environ["BINANCE_SECRET_KEY"]
    client = Client(binance_api_key, binance_secret_key)
    # Which pair you want to trade
    symbol = "BTCUSDT"
    # Number of delay windows allowed to trigger a buy according to the stochastic indicator
    lags = 3

    stop_limit_percentage = 0.999
    stop_loss_percentage = 1.005
    rsi_window = 14
    rsi_buying_trigger = 30
    rsi_selling_trigger = 70
    macd_window_slow = 26
    macd_window_fast = 12
    macd_window_sign = 9
    stoch_window = 14
    stoch_smooth_window = 3
    stoch_limits = [20, 80]

    # # Candle size
    # interval = Client.KLINE_INTERVAL_1WEEK
    # simu_market_start_timestamp = date_to_mili_timestamp('01.01.2020 02:00:00')
    # # WARNING, you need at least 33 iterations between the beginning and the end for MACD
    # simu_market_stop_timestamp = date_to_mili_timestamp('04.09.2020 02:00:00')

    # history_start_timestamp = date_to_mili_timestamp('07.09.2020 02:00:00')
    # history_stop_timestamp = date_to_mili_timestamp('20.06.2022 02:00:00')

    # Candle size
    interval = Client.KLINE_INTERVAL_1MINUTE
    simu_market_start_timestamp = date_to_mili_timestamp("09.07.2022 00:00:00")
    # WARNING, you need at least 33 iterations between the beginning and the end for MACD
    simu_market_stop_timestamp = date_to_mili_timestamp("09.07.2022 04:00:00")

    # history_start_timestamp needs to start 1 interval right after the end of simu_market
    history_start_timestamp = date_to_mili_timestamp("09.07.2022 04:01:00")
    history_stop_timestamp = date_to_mili_timestamp("09.07.2022 05:00:00")

    market_data_history = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=history_start_timestamp,
        end_str=history_stop_timestamp,
    )

    # INDICATORS
    rsi_indicator = RsiIndicator(
        rsi_window=rsi_window,
        rsi_buying_trigger=rsi_buying_trigger,
        rsi_selling_trigger=rsi_selling_trigger,
    )

    macd_indicator = MacdIndicator(
        macd_window_slow=macd_window_slow,
        macd_window_fast=macd_window_fast,
        macd_window_sign=macd_window_sign,
    )

    stochastic_indicator = StochasticIndicator(
        lags=lags,
        stoch_window=stoch_window,
        stoch_smooth_window=stoch_smooth_window,
        stoch_limits=stoch_limits,
    )

    sma7_indicator = Sma7Indicator()
    sma20_indicator = Sma20Indicator()
    sma50_indicator = Sma50Indicator()
    sma100_indicator = Sma100Indicator()
    sma200_indicator = Sma200Indicator()

    simu_market_data = MarketData(
        symbol=symbol,
        interval=interval,
        lags=lags,
        start_str=simu_market_start_timestamp,
        end_str=simu_market_stop_timestamp,
        client=client,
        indicators=[
            rsi_indicator,
            macd_indicator,
            stochastic_indicator,
            sma7_indicator,
            sma20_indicator,
            sma50_indicator,
            sma100_indicator,
            sma200_indicator,
        ],
        stop_limit_percentage=stop_limit_percentage,
        stop_loss_percentage=stop_loss_percentage,
    )

    mock_client = MockClient(market_data_history=market_data_history)
    simu_market_data.client = mock_client

    while len(market_data_history) > 1:
        strategy_testing(
            market_data=simu_market_data,
            market_data_history=market_data_history,
            sleep_time=0,
        )
        simu_market_data.update_data()

    assert (
        simu_market_data.df["Bought"].sum() - simu_market_data.df["Sold"].sum()
    ) in [0, 1], "Buy/Sell mismatch O_o"

    impact = float("%.2f" % get_impact(simu_market_data.df))
    print(f"Impact: {impact} %")

    df = simu_market_data.df
    simu_market_data.show_candlestick_with_plotly()
