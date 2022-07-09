import numpy as np
import pandas as pd
from binance import Client
import ta


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
        stop_limit_percentage=0.999,
        stop_loss_percentage=1.005,
        rsi_trigger=30,
        rsi_window=14,
        macd_window_slow=26,
        macd_window_fast=12,
        macd_window_sign=9,
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
        self.stop_limit_percentage = stop_limit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.rsi_trigger = rsi_trigger
        self.rsi_window = rsi_window
        self.macd_window_slow = macd_window_slow
        self.macd_window_fast = macd_window_fast
        self.macd_window_sign = macd_window_sign
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
        # On prend et renomme que les 6 premières colonnes
        frame = frame.iloc[:, :6]
        frame.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
        frame["Timestamp"] = frame["Time"]
        frame = frame.set_index("Time")
        frame.index = pd.to_datetime(frame.index, unit="ms")
        # Initiate
        frame[["%K", "%D", "RSI", "MACD"]] = np.nan
        frame[["Buy", "Bought", "Sell", "trigger"]] = 0
        return frame.astype(float)

    def update_data(self):
        """Get the new line for the latest candle, concatenate it with the rest and apply_technicals to it"""
        # TODO: Là on recalcule toutes les lignes à chaque update; il faut faire plus intelligemment
        start_str = int(self.df.Timestamp[-1])
        # end_str is on interval after start_str
        end_str = int(start_str * 2 - self.df.Timestamp[-2])
        new_candle = self._get_data(start_str=start_str, end_str=end_str)
        # reset indexes to ease to add of new row
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
        # What is smooth window ?
        self.df["%K"] = ta.momentum.stoch(
            self.df.High,
            self.df.Low,
            self.df.Close,
            window=self.stoch_window,
            smooth_window=0,
        )
        self.df["%D"] = self.df["%K"].rolling(self.stoch_smooth_window).mean()
        self.df["RSI"] = ta.momentum.rsi(self.df.Close, window=self.rsi_window)
        # MACD est à affiner; on ne prend ici que la diff des deux courbes
        self.df["MACD"] = ta.trend.macd_diff(
            self.df.Close,
            self.macd_window_slow,
            self.macd_window_fast,
            self.macd_window_sign,
        )

    def get_stoch_trigger(self):
        """Shifts `self.lags` times the stochastic indicator for each dates.
        Each dates has `self.lags` bools, if one of them is True then is it seen as a trigger"""
        masks = [
            # soit on est dans une zone de survente
            (self.df["%K"].shift(i) < self.stoch_trigger)
            & (self.df["%D"].shift(i) < self.stoch_trigger)
            for i in range(self.lags + 1)
        ]
        return pd.DataFrame(masks).sum(axis=0)

    def get_stoch_cross_trigger(self):
        """Shifts `self.lags` times the stochastic indicator for each dates.
        Each dates has `self.lags` bools, if one of them is True then is it seen as a trigger"""
        masks = [
            # soit il y a un croisement des courbes %K et %D
            (self.df["%K"].shift(i) > self.df["%D"].shift(i))
            & (self.df["%K"].shift(i + 1) < self.df["%D"].shift(i + 1))
            for i in range(self.lags + 1)
        ]
        return pd.DataFrame(masks).sum(axis=0)

    def decide(self):
        """Creates two new columns:
        'trigger' : stochastic indicator shows that the assets was oversold at last date
        'Buy': decision to buy or not.
        Is needed to buy:
            - Trigger as True.
            - %K and %D back in between 20 and 80.
            - RSI above self.rsi_trigger.
            - MACD > 0. It means that EMA of diff of slow/fast EMA is greater than diff of slow/fast EMA
        """
        self.df["trigger"] = np.where(self.get_stoch_trigger(), 1, 0)
        self.df["cross_trigger"] = np.where(self.get_stoch_cross_trigger(), 1, 0)

        stoch_trigger_indicator = (
            self.df.trigger
            & self.df["%K"].between(self.stoch_limits[0], self.stoch_limits[1])
            & self.df["%D"].between(self.stoch_limits[0], self.stoch_limits[1])
        )

        stoch_cross_trigger_indicator = self.df.cross_trigger & (
            self.df["%K"] > self.df["%D"]
        )

        buying_conditions = (
            (stoch_trigger_indicator | stoch_cross_trigger_indicator)
            & (self.df.RSI > self.rsi_trigger)
            & (self.df.MACD > 0)
        )
        self.df["Buy"] = np.where(buying_conditions, 1, 0)
