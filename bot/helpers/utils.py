import ast
import os
import random
from datetime import datetime

from binance import Client

from bot.logging_formatter import logger


def load_market_data_history(
    client, symbol, interval, history_start_timestamp, history_stop_timestamp
):
    history_path = f"./data/{history_start_timestamp}-{history_stop_timestamp}-history"
    if os.path.exists(history_path):
        logger.debug("::Loading:: market_data_history from local storage")
        market_data_history = []
        # open file and read the content in a list
        with open(history_path, "r") as fp:
            for line in fp:
                # remove linebreak from a current name
                x = line[:-1]
                # add current item to the list
                market_data_history.append(ast.literal_eval(x))
    else:
        logger.debug("::Loading:: market_data_history from client")
        market_data_history = client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=history_start_timestamp,
            end_str=history_stop_timestamp,
        )
        with open(history_path, "w") as fp:
            for item in market_data_history:
                # write each item on a new line
                fp.write("%s\n" % item)
    return market_data_history


def date_to_mili_timestamp(date):
    return int(datetime.strptime(date, "%d.%m.%Y %H:%M:%S").timestamp() * 1000)


def interval_to_mili_timestamp(interval):
    # hours, minutes, seconds = 2, 0, 0
    # refresh_frequency = float(3600000 * hours + 60000 * minutes + 1000 * seconds)
    match interval:
        case Client.KLINE_INTERVAL_1MINUTE:
            return int(60000 * 1)
        case Client.KLINE_INTERVAL_1HOUR:
            return int(3600000 * 1)
        case Client.KLINE_INTERVAL_2HOUR:
            return int(3600000 * 2)
        case Client.KLINE_INTERVAL_4HOUR:
            return int(3600000 * 4)


def get_random_color() -> str:
    return "#" + "".join([random.choice("ABCDEF0123456789") for i in range(6)])


def merge_candles(old_candle, new_candle):
    """
    Take two consecutive candles and merge them together
    :param old_candle: old candle to take value from
    :param new_candle: new candle to update value to
    :return:
    """
    new_candle.at[new_candle.index[-1], "OpenTime"] = old_candle["OpenTime"].iloc[-1]
    new_candle.at[new_candle.index[-1], "OpenDate"] = old_candle["OpenDate"].iloc[-1]
    new_candle.at[new_candle.index[-1], "Open"] = old_candle["Open"].iloc[-1]
    new_candle.at[new_candle.index[-1], "High"] = max(
        new_candle["High"].iloc[-1], old_candle["High"].iloc[-1]
    )
    new_candle.at[new_candle.index[-1], "Low"] = min(
        new_candle["Low"].iloc[-1], old_candle["Low"].iloc[-1]
    )
    new_candle.at[new_candle.index[-1], "Volume"] = (
        new_candle["Volume"].iloc[-1] + old_candle["Volume"].iloc[-1]
    )
    return new_candle
