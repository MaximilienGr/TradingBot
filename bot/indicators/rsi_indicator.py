import ta
from plotly.graph_objs import Scatter

from bot.indicators.indicator import Indicator


class RsiIndicator(Indicator):
    def __init__(self, rsi_window, rsi_buying_trigger, rsi_selling_trigger, **kwargs):
        super().__init__(**kwargs)
        self.rsi_window = rsi_window
        self.rsi_buying_trigger = rsi_buying_trigger
        self.rsi_selling_trigger = rsi_selling_trigger

    def set_indicator(self, df):
        # TODO: pourquoi les premières valeurs sont à 0 ? Avant c'était des NaN
        df["RSI"] = ta.momentum.rsi(df.Close, window=self.rsi_window)
        return df

    def should_long(self, df):
        if df["RSI"].iloc[-1] > self.rsi_buying_trigger:
            return True
        return False

    def should_short(self, df):
        if df["RSI"].iloc[-1] > self.rsi_selling_trigger:
            return True
        return False

    def get_plot_scatters(self, df) -> list[Scatter]:
        return []
