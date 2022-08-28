import ast
import os
import random
from datetime import datetime

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


def get_random_color() -> str:
    return "#" + "".join([random.choice("ABCDEF0123456789") for i in range(6)])
