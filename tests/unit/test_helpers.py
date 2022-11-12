import pandas as pd
from binance import Client

from bot.helpers.utils import (
    date_to_mili_timestamp,
    interval_to_mili_timestamp,
    merge_candles,
)


class TestHelpers:
    def test_merge_candles(self):
        old_candle_data = {
            "OpenTime": {0: 1641700800000.0},
            "Open": {0: 41833.9},
            "High": {0: 42103.31},
            "Low": {0: 41800.78},
            "Close": {0: 42079.41},
            "Volume": {0: 884.47963},
            "CloseTime": {0: 1641704399999.0},
            "LongSignal": {0: True},
            "ShortSignal": {0: True},
            "LongPosition": {0: True},
            "ShortPosition": {0: True},
            "isClosed": {0: True},
            "OpenDate": {0: pd.Timestamp("2022-01-09 04:00:00")},
            "CloseDate": {0: pd.Timestamp("2022-01-09 04:59:59.999000064")},
        }
        new_candle_data = {
            "OpenTime": {0: 1641704400000.0},
            "Open": {0: 42079.4},
            "High": {0: 42097.44},
            "Low": {0: 41715.44},
            "Close": {0: 41765.9},
            "Volume": {0: 594.21526},
            "CloseTime": {0: 1641707999999.0},
            "LongSignal": {0: False},
            "ShortSignal": {0: False},
            "LongPosition": {0: False},
            "ShortPosition": {0: False},
            "isClosed": {0: False},
            "OpenDate": {0: pd.Timestamp("2022-01-09 05:00:00")},
            "CloseDate": {0: pd.Timestamp("2022-01-09 05:59:59.999000064")},
        }
        expected_candle_data = {
            "OpenTime": {0: 1641700800000.0},
            "Open": {0: 41833.9},
            "High": {0: 42103.31},
            "Low": {0: 41715.44},
            "Close": {0: 41765.9},
            "Volume": {0: 594.21526 + 884.47963},
            "CloseTime": {0: 1641707999999.0},
            "LongSignal": {0: True},
            "ShortSignal": {0: True},
            "LongPosition": {0: True},
            "ShortPosition": {0: True},
            "isClosed": {0: True},
            "OpenDate": {0: pd.Timestamp("2022-01-09 04:00:00")},
            "CloseDate": {0: pd.Timestamp("2022-01-09 05:59:59.999000064")},
        }
        old_candle = pd.DataFrame(data=old_candle_data)
        new_candle = pd.DataFrame(data=new_candle_data)
        expected_candle = pd.DataFrame(data=expected_candle_data)
        merged_candle = merge_candles(old_candle, new_candle)

        assert merged_candle.compare(expected_candle).empty

    def test_interval_to_mili_timestamp(self):
        assert interval_to_mili_timestamp(Client.KLINE_INTERVAL_1MINUTE) == 60000
        assert interval_to_mili_timestamp(Client.KLINE_INTERVAL_1HOUR) == 3600000
        assert interval_to_mili_timestamp(Client.KLINE_INTERVAL_2HOUR) == 7200000
        assert interval_to_mili_timestamp(Client.KLINE_INTERVAL_4HOUR) == 14400000

    def test_date_to_mili_timestamp(self):
        assert date_to_mili_timestamp("01.01.2020 02:00:00") == 1577840400000
