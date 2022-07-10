import numpy as np
import pandas as pd
from binance import Client

from indicators.indicator import Indicator


class MarketData:
    def __init__(
        self,
        start_str,
        end_str,
        data=None,
        symbol="BTCUSDT",
        interval=Client.KLINE_INTERVAL_1MINUTE,
        lags=5,
        client=None,
        indicators=None,
        stop_limit_percentage=0.999,
        stop_loss_percentage=1.005,
        stoch_window=14,
        stoch_smooth_window=3,
        stoch_trigger=20,
        stoch_limits=[20, 80],
    ):
        self.symbol = symbol
        self.interval = interval
        self.start_str = start_str
        self.end_str = end_str
        self.lags = lags
        self.client = client
        self.indicators: list[Indicator] = indicators
        self.stop_limit_percentage = stop_limit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.stoch_window = stoch_window
        self.stoch_smooth_window = stoch_smooth_window
        self.stoch_trigger = stoch_trigger
        self.stoch_limits = stoch_limits
        if not data:
            data = self._get_data(start_str=self.start_str, end_str=self.end_str)
        self.df = pd.DataFrame(data)
        self.apply_technicals()

    def should_buy(self):
        return bool(self.df.Buy.iloc[-1])

    def should_sell(self, buy_price):
        stop_loss_activated = self.df.Close[-1] <= buy_price * self.stop_loss_percentage
        stop_limit_activated = (
            self.df.Close[-1] >= buy_price * self.stop_limit_percentage
        )
        return stop_loss_activated or stop_limit_activated

    def _get_data(self, start_str, end_str):
        """Get all data from binance
        :param start_str : Timestamp to start fetching data from.
        :param end_str: Timestamp to stop fetching data from"""
        frame = pd.DataFrame(
            self.client.get_historical_klines(
                symbol=self.symbol,
                interval=self.interval,
                start_str=start_str,
                end_str=end_str,
            )
        )
        # Formatting the data
        frame = frame.iloc[:, :6]
        frame.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
        frame["Timestamp"] = frame["Time"]
        frame = frame.set_index("Time")
        frame.index = pd.to_datetime(frame.index, unit="ms")
        frame[["%K", "%D", "RSI", "MACD"]] = np.nan
        frame[["Buy", "Bought", "Sell"]] = 0
        return frame.astype(float)

    def update_data(self):
        """Get the new line for the latest candle, concatenate it with the rest and apply_technicals to it"""
        # TODO: Là on recalcule toutes les lignes à chaque update; il faut faire plus intelligemment
        start_str = int(self.df.Timestamp[-1])
        # end_str is on interval after start_str
        end_str = int(start_str * 2 - self.df.Timestamp[-2])
        new_candle = self._get_data(start_str=start_str, end_str=end_str)
        # reset indexes to ease the adding of the new row
        df = self.df.reset_index()
        new_candle = new_candle.reset_index()
        # Add the rows
        df = pd.concat([df, new_candle], ignore_index=True)
        # set back index
        self.df = df.set_index("Time")
        self.df = self.df[~self.df.index.duplicated(keep="first")]
        self.apply_technicals()

    def apply_technicals(self):
        """Make the maths for all indicators"""
        for indicator in self.indicators:
            self.df = indicator.set_indicator(df=self.df)

    def decide(self):
        """Creates two new columns:
        'Buy': decision to buy or not.
        'Sell': decision to sell or not.
        Is needed to buy to have all the indicators sending True
        """
        should_buy = False
        for indicator in self.indicators:
            should_buy = indicator.should_buy(df=self.df) and should_buy

        should_sell = False
        for indicator in self.indicators:
            if indicator.should_sell(df=self.df):
                breakpoint()
            should_sell = indicator.should_sell(df=self.df) and should_sell

        self.df["Buy"] = should_buy
        self.df["Sell"] = should_sell
