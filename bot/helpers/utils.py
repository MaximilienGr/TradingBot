import ast
import csv
import logging
import os
import random
import re
from collections import deque
from pathlib import Path

import numpy as np
from dateutil import parser
from pandas import DataFrame, Timestamp
from scipy.signal import argrelextrema

from .types import ExtremaDirection, ExtremaType


def save_list_as_csv(start_str, end_str, interval, list):
    history_path = f"./data/market_data/{start_str}-{end_str}-{interval}-history.csv"
    Path(history_path).parent.mkdir(parents=True, exist_ok=True)
    if not os.path.exists(history_path):
        with open(history_path, "w") as fp:
            wr = csv.writer(fp, delimiter="\n")
            wr.writerows(list)


def load_market_data_history(
    client, symbol, refresh_frequency, history_start_timestamp, history_stop_timestamp
):
    history_path = f"./data/market_data/{history_start_timestamp}-{history_stop_timestamp}-{refresh_frequency}-history"
    Path(history_path).parent.mkdir(parents=True, exist_ok=True)
    if os.path.exists(history_path):
        logging.info("::Loading:: market_data_history from local storage")
        market_data_history = []
        # open file and read the content in a list
        with open(history_path, "r") as fp:
            for line in fp:
                # remove linebreak from a current name
                x = line[:-1]
                # add current item to the list
                market_data_history.append(ast.literal_eval(x))
    else:
        logging.info("::Loading:: market_data_history from client")
        market_data_history = client.get_historical_klines(
            symbol=symbol,
            interval=refresh_frequency,
            start_str=history_start_timestamp,
            end_str=history_stop_timestamp,
        )
        with open(history_path, "w") as fp:
            for item in market_data_history:
                # write each item on a new line
                fp.write("%s\n" % item)
    return market_data_history


def date_to_mili_timestamp(date):
    return int(parser.parse(date, dayfirst=True).timestamp() * 1000)


def interval_to_mili_timestamp(interval):
    # hours, minutes, seconds = 2, 0, 0
    # refresh_frequency = float(3600000 * hours + 60000 * minutes + 1000 * seconds)
    match re.split(r"(\d+)", interval)[1:]:
        case [number, "m"]:
            return 60000 * int(number)
        case [number, "h"]:
            return 60000 * 60 * int(number)
        case [number, "d"]:
            return 60000 * 60 * 24 * int(number)
        case [number, "w"]:
            return 60000 * 60 * 24 * 7 * int(number)
        case [number, "M"]:
            logging.warning(
                "Watchout with the intervals... Interval for months are not very precise ? 30d ? 31d ?"
            )
            return 60000 * 60 * 24 * 7 * 30 * int(number)


def get_random_color() -> str:
    return "#" + "".join([random.choice("ABCDEF0123456789") for i in range(6)])


def merge_candles(old_candle, new_candle):
    """
    Take two consecutive candles and merge them together
    :param old_candle: old candle to take value from
    :param new_candle: new candle to update value to
    :return:
    """
    old_candle.at[old_candle.index[-1], "CloseTime"] = new_candle["CloseTime"].iloc[-1]
    old_candle.at[old_candle.index[-1], "CloseDate"] = new_candle["CloseDate"].iloc[-1]
    old_candle.at[old_candle.index[-1], "Close"] = new_candle["Close"].iloc[-1]
    old_candle.at[old_candle.index[-1], "High"] = max(
        old_candle["High"].iloc[-1], new_candle["High"].iloc[-1]
    )
    old_candle.at[old_candle.index[-1], "Low"] = min(
        old_candle["Low"].iloc[-1], new_candle["Low"].iloc[-1]
    )
    old_candle.at[old_candle.index[-1], "Volume"] = (
        old_candle["Volume"].iloc[-1] + new_candle["Volume"].iloc[-1]
    )
    return old_candle


def get_extrema(
    df: DataFrame,
    order: int = 5,
    K: int = 2,
    extrema_direction: ExtremaDirection = ExtremaDirection.HIGHER,
    extrema_type: ExtremaType = ExtremaType.HIGHS,
):
    """
    Finds consecutive peaks in price pattern.
    Must not be exceeded within the number of periods indicated by the width
    parameter for the value to be confirmed.
    K determines how many consecutive peaks need to be higher/lower.
    """
    # Get extremas
    np_method = np.greater if extrema_type == ExtremaType.HIGHS else np.less
    extrema_idx = argrelextrema(df, np_method, order=order)[0]
    extremas = df[extrema_idx]

    # Ensure consecutive highs are higher than previous highs
    extrema = []
    ex_deque: deque = deque(maxlen=K)

    for i, idx in enumerate(extrema_idx):
        if i == 0:
            ex_deque.append(idx)
            continue

        if (
            extremas[i] < extremas[i - 1]
            and extrema_direction == ExtremaDirection.HIGHER
        ) or (
            extremas[i] > extremas[i - 1]
            and extrema_direction == ExtremaDirection.LOWER
        ):
            ex_deque.clear()

        ex_deque.append(idx)
        if len(ex_deque) == K:
            extrema.append(ex_deque.copy())

    return extrema


def get_extrema_index(df: DataFrame, extrema: list, order: int = 5) -> list:
    idx = np.array([i[-1] + order for i in extrema])
    return idx[np.where(idx < len(df))]


def get_extremum_between_range(df, x1, x2) -> tuple[float, float]:
    """
    Return the extremum between two dates
    :param x1: first timestamp
    :param x2: second timestamp
    :return:  tuple of two extremums
    """
    if x1 > x2:
        x1, x2 = x2, x1

    ymin = df.loc[
        df["CloseDate"].between(
            left=Timestamp(x1),
            right=Timestamp(x2),
            inclusive="neither",
        ),
        "Low",
    ].min()
    ymax = df.loc[
        df["CloseDate"].between(
            left=Timestamp(x1),
            right=Timestamp(x2),
            inclusive="neither",
        ),
        "High",
    ].max()
    return (ymin, ymax)


def _ansi_style(value: str, *styles: str) -> str:
    codes = {
        "bold": 1,
        "red": 31,
        "green": 32,
        "yellow": 33,
        "magenta": 35,
        "cyan": 36,
    }

    for style in styles:
        value = f"\x1b[{codes[style]}m{value}"

    return f"{value}\x1b[0m"
