import logging
import os

from binance.client import Client

from bot.helpers.utils import load_market_data_history
from bot.logging_formatter import logger
from bot.marketdata import MarketData
from bot.mock.mock_client import MockClient
from bot.profitability import get_impact
from bot.strategy import strategy_testing
from bot.utils import date_to_mili_timestamp

from bot.indicators.macd_indicator import MacdIndicator
from bot.indicators.rsi_indicator import RsiIndicator
from bot.indicators.stochastic_indicator import StochasticIndicator
from bot.indicators.sma9_21_indicator import Sma9_21Indicator
from bot.indicators.sma_indicator import SmaIndicator


if __name__ == "__main__":
    logger.warning("Let's start dat shit: warning")
    logger.debug("Let's start dat shit: debug")
    logger.info("Let's start dat shit: info")  # green
    logger.error("Let's start dat shit: error")  # red
    logger.critical("Let's start dat shit: critical")

    binance_api_key = os.environ["BINANCE_API_KEY"]
    binance_secret_key = os.environ["BINANCE_SECRET_KEY"]
    client = Client(binance_api_key, binance_secret_key)

    # Which pair you want to trade
    symbol = "BTCUSDT"
    # Number of delay windows allowed to trigger a buy according to the stochastic indicator
    lags = 3

    stop_loss_percentage = 0.95
    stop_limit_percentage = 2
    # rsi_window = 14
    # rsi_buying_trigger = 30
    # rsi_selling_trigger = 70
    # macd_window_slow = 26
    # macd_window_fast = 12
    # macd_window_sign = 9
    # stoch_window = 14
    # stoch_smooth_window = 3
    # stoch_limits = [20, 80]

    # # Candle size
    # interval = Client.KLINE_INTERVAL_1WEEK
    # simu_market_start_timestamp = date_to_mili_timestamp('01.01.2020 02:00:00')
    # # WARNING, you need at least 33 iterations between the beginning and the end for MACD
    # simu_market_stop_timestamp = date_to_mili_timestamp('04.09.2020 02:00:00')

    # history_start_timestamp = date_to_mili_timestamp('07.09.2020 02:00:00')
    # history_stop_timestamp = date_to_mili_timestamp('20.06.2022 02:00:00')

    # Candle size
    interval = Client.KLINE_INTERVAL_4HOUR
    simu_market_start_timestamp = date_to_mili_timestamp("03.01.2022 00:00:00")
    # WARNING, you need at least 33 iterations between the beginning and the end for MACD
    simu_market_stop_timestamp = date_to_mili_timestamp("09.01.2022 04:00:00")

    # history_start_timestamp needs to start 1 interval right after the end of simu_market
    history_start_timestamp = date_to_mili_timestamp("09.01.2022 08:00:00")
    history_stop_timestamp = date_to_mili_timestamp("23.08.2022 18:00:00")

    market_data_history = load_market_data_history(
        client, symbol, interval, history_start_timestamp, history_stop_timestamp
    )

    # INDICATORS
    # rsi_indicator = RsiIndicator(
    #     rsi_window=rsi_window,
    #     rsi_buying_trigger=rsi_buying_trigger,
    #     rsi_selling_trigger=rsi_selling_trigger,
    # )
    #
    # macd_indicator = MacdIndicator(
    #     macd_window_slow=macd_window_slow,
    #     macd_window_fast=macd_window_fast,
    #     macd_window_sign=macd_window_sign,
    # )
    #
    # stochastic_indicator = StochasticIndicator(
    #     lags=lags,
    #     stoch_window=stoch_window,
    #     stoch_smooth_window=stoch_smooth_window,
    #     stoch_limits=stoch_limits,
    # )

    sma9_21_indicator = Sma9_21Indicator()

    simu_market_data = MarketData(
        symbol=symbol,
        interval=interval,
        lags=lags,
        start_str=simu_market_start_timestamp,
        end_str=simu_market_stop_timestamp,
        client=client,
        indicators=[
            sma9_21_indicator,
            # rsi_indicator,
            # macd_indicator,
            # stochastic_indicator,
            # SmaIndicator(7),
            # SmaIndicator(9),
            # SmaIndicator(20),
            # SmaIndicator(50),
            # SmaIndicator(100),
            # SmaIndicator(200),
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
        simu_market_data.df["BuyingSignal"].sum()
        - simu_market_data.df["SellingSignal"].sum()
    ) in [0, 1], "Buy/Sell mismatch O_o"

    initial_investment = 1000
    wallet = float("%.2f" % get_impact(simu_market_data.df, initial_investment))
    rentability_percentage = 100 * (wallet - initial_investment) / initial_investment
    print(
        f"For an initial investment of {initial_investment} $: {wallet}."
        f" --> {round(rentability_percentage, 2)} %"
    )

    df = simu_market_data.df
    # simu_market_data.show_candlestick_with_plotly()
