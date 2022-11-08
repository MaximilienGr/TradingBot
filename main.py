import os

from binance.client import Client

from bot.display import setup_dash
from bot.helpers.utils import (
    load_market_data_history,
    date_to_mili_timestamp,
)

# from bot.indicators.rsi_indicator import RsiIndicator
from bot.logging_formatter import logger
from bot.tradingbot import TradingBot
from bot.client.mock_client import MockClient
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

    #########################################################
    #                  General parameters                   #
    #########################################################
    # Which pair you want to trade
    SYMBOL = "BTCUSDT"
    # Money initially invested
    PORTFOLIO = 1000
    # Losing percentage admitted before quiting position. 0.05 == 5%
    STOP_LOSS_PERCENTAGE = 0.05
    # Maximum wining percentage admitted before quiting position 1 == 100%
    STOP_LIMIT_PERCENTAGE = 1

    logger.info("Trading %s", SYMBOL)  # yellow
    logger.info("Initial investment %s", PORTFOLIO)  # yellow

    #########################################################
    #                  Time parameters parameters           #
    #########################################################
    # Candle size
    INTERVAL = Client.KLINE_INTERVAL_1DAY
    REFRESH_FREQUENCY = Client.KLINE_INTERVAL_1DAY
    simu_market_start_timestamp = date_to_mili_timestamp("03.01.2022 00:00:00 GMT")
    # WARNING, you need at least 33 iterations between the beginning and the end for MACD
    simu_market_stop_timestamp = date_to_mili_timestamp("09.02.2022 00:00:00 GMT")

    history_start_timestamp = simu_market_stop_timestamp
    history_stop_timestamp = date_to_mili_timestamp("26.09.2022 18:00:00")

    #########################################################
    #    All indicator that will be used to decide          #
    #########################################################
    sma9_21_indicator = Sma9_21Indicator()
    # rsi_indicator = RsiIndicator()

    #########################################################
    #  Main object. Containing all the data and decisions   #
    #########################################################
    simu_trading_bot = TradingBot(
        start_str=simu_market_start_timestamp,
        end_str=simu_market_stop_timestamp,
        symbol=SYMBOL,
        portfolio=PORTFOLIO,
        interval=INTERVAL,
        client=client,
        indicators=[
            sma9_21_indicator,
            # rsi_indicator,
        ],
        stop_limit_percentage=STOP_LIMIT_PERCENTAGE,
        stop_loss_percentage=STOP_LOSS_PERCENTAGE,
        refresh_frequency=REFRESH_FREQUENCY,
    )

    #########################################################
    #     Trick to simulate a client with all market data   #
    #########################################################
    market_data_history = load_market_data_history(
        client,
        SYMBOL,
        REFRESH_FREQUENCY,
        history_start_timestamp,
        history_stop_timestamp,
    )
    mock_client = MockClient(market_data_history=market_data_history)
    simu_trading_bot.df.isClosed = True
    simu_trading_bot.client = mock_client

    while len(market_data_history) > 1:
        strategy_testing(trading_bot=simu_trading_bot)

    #########################################################
    #     Setting up dash server for Graphical analyse      #
    #########################################################
    setup_dash(simu_trading_bot)
