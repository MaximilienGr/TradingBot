import ta
from plotly.graph_objs import Scatter

from bot.indicators.indicator import Indicator


class MacdIndicator(Indicator):
    def __init__(self, macd_window_slow, macd_window_fast, macd_window_sign, **kwargs):
        super().__init__(**kwargs)
        self.macd_window_slow = macd_window_slow
        self.macd_window_fast = macd_window_fast
        self.macd_window_sign = macd_window_sign

    def set_indicator(self, df):
        df["MACD"] = ta.trend.macd_diff(
            df.Close,
            self.macd_window_slow,
            self.macd_window_fast,
            self.macd_window_sign,
        )
        return df

    def should_buy(self, df):
        if df["MACD"].iloc[-1] > 0:
            return True
        return False

    def should_sell(self, df):
        if df["MACD"].iloc[-1] < 0:
            return True
        return False

    def get_plot_scatters(self, df) -> list[Scatter]:
        return []
