import os

from binance.client import Client

from bot.helpers.utils import (
    load_market_data_history,
    date_to_mili_timestamp,
)
from bot.logging_formatter import logger
from bot.marketdata import MarketData
from bot.mock.mock_client import MockClient
from bot.strategy import strategy_testing

from bot.indicators.sma9_under_sma21_indicator import Sma9_21Indicator


if __name__ == "__main__":
    logger.warning("Let's start dat shit: warning")  # yellow
    logger.debug("Let's start dat shit: debug")  # pruple
    logger.info("Let's start dat shit: info")  # green
    logger.error("Let's start dat shit: error")  # red

    binance_api_key = os.environ["BINANCE_API_KEY"]
    binance_secret_key = os.environ["BINANCE_SECRET_KEY"]
    client = Client(binance_api_key, binance_secret_key)

    # Which pair you want to trade
    symbol = "BTCUSDT"
    logger.warning(f"Trading {symbol}")  # yellow
    # Number of delay windows allowed to trigger a buy according to the stochastic indicator
    lags = 3
    # Money initially invested
    portfolio = 1000
    logger.warning(f"Initial investment {portfolio}")  # yellow

    # Losing percentage admitted before quiting position. 0.05 == 5%
    stop_loss_percentage = 0.05
    # Maximum wining percentage admitted before quiting position 1 == 100%
    stop_limit_percentage = 1

    # Candle size
    interval = Client.KLINE_INTERVAL_1DAY
    refresh_frequency = Client.KLINE_INTERVAL_1DAY
    simu_market_start_timestamp = date_to_mili_timestamp("03.01.2022 00:00:00")
    # WARNING, you need at least 33 iterations between the beginning and the end for MACD
    simu_market_stop_timestamp = date_to_mili_timestamp("09.02.2022 04:00:00")

    history_start_timestamp = simu_market_stop_timestamp
    history_stop_timestamp = date_to_mili_timestamp("23.08.2022 18:00:00")

    market_data_history = load_market_data_history(
        client,
        symbol,
        refresh_frequency,
        history_start_timestamp,
        history_stop_timestamp,
    )

    ### INDICATORS
    sma9_21_indicator = Sma9_21Indicator()

    simu_market_data = MarketData(
        start_str=simu_market_start_timestamp,
        end_str=simu_market_stop_timestamp,
        symbol=symbol,
        portfolio=portfolio,
        interval=interval,
        lags=lags,
        client=client,
        indicators=[sma9_21_indicator],
        stop_limit_percentage=stop_limit_percentage,
        stop_loss_percentage=stop_loss_percentage,
        refresh_frequency=refresh_frequency,
    )

    mock_client = MockClient(market_data_history=market_data_history)
    simu_market_data.df.isClosed = True
    simu_market_data.client = mock_client

    while len(market_data_history) > 1:
        strategy_testing(market_data=simu_market_data)

    assert (
        abs(
            simu_market_data.df["LongPosition"].sum()
            - simu_market_data.df["ShortPosition"].sum()
        )
    ) in [0, 1], "Buy/Sell mismatch O_o"

    simu_market_data.show_candlestick_with_plotly()
