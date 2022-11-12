import os

from binance.client import Client

from bot.helpers.utils import (
    date_to_mili_timestamp,
    interval_to_mili_timestamp,
    save_list_as_csv,
)
from bot.logging_formatter import logger

if __name__ == "__main__":
    binance_api_key = os.environ["BINANCE_API_KEY"]
    binance_secret_key = os.environ["BINANCE_SECRET_KEY"]
    client = Client(binance_api_key, binance_secret_key)

    symbol = "BTCUSDT"

    # Candle size
    interval = Client.KLINE_INTERVAL_1HOUR

    start_str = "01.03.2019 00:00:00"
    end_str = "20.09.2022 00:00:00"

    logger.debug(
        f"Loading data between {start_str} and {end_str} for {symbol} with interval {interval}"
    )

    market_data = client.get_historical_klines(
        symbol=symbol,
        interval=interval,
        start_str=date_to_mili_timestamp(start_str),
        end_str=date_to_mili_timestamp(end_str),
    )
    for i in range(len(market_data) - 1):
        if market_data[i + 1][0] - market_data[i][0] != interval_to_mili_timestamp(
            interval
        ):
            raise Exception

    save_list_as_csv(
        start_str=date_to_mili_timestamp(start_str),
        end_str=date_to_mili_timestamp(end_str),
        interval=interval,
        list=market_data,
    )
