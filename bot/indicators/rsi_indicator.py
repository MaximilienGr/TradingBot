import ta

from . import indicator


class RsiIndicator(indicator.Indicator):
    def __init__(self, rsi_window, rsi_buying_trigger, rsi_selling_trigger, **kwargs):
        super().__init__(**kwargs)
        self.rsi_window = rsi_window
        self.rsi_buying_trigger = rsi_buying_trigger
        self.rsi_selling_trigger = rsi_selling_trigger

    def set_indicator(self, df):
        # TODO: pourquoi les premières valeurs sont à 0 ? Avant c'était des NaN
        df["RSI"] = ta.momentum.rsi(df.Close, window=self.rsi_window)
        return df

    def should_buy(self, df):
        if df["RSI"].iloc[-1] > self.rsi_buying_trigger:
            return True
        return False

    def should_sell(self, df):
        if df["RSI"].iloc[-1] < self.rsi_selling_trigger:
            return True
        return False
