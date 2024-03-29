from plotly.graph_objs import Scatter
from ta import trend

from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class MACDIndicator(Indicator):
    type = IndicatorType.MOMENTUM_OSCILLATOR

    def __init__(self, macd_window_slow, macd_window_fast, macd_window_sign, **kwargs):
        super().__init__(**kwargs)
        self.macd_window_slow = macd_window_slow
        self.macd_window_fast = macd_window_fast
        self.macd_window_sign = macd_window_sign

    def set_indicator(self, df):
        df[("indicators", "MACD")] = trend.macd_diff(
            df.Close,
            self.macd_window_slow,
            self.macd_window_fast,
            self.macd_window_sign,
        )
        return df

    def should_long(self, df):
        if df[("indicators", "MACD")].iloc[-1] > 0:
            return True
        return False

    def should_short(self, df):
        if df[("indicators", "MACD")].iloc[-1] < 0:
            return True
        return False

    def should_quit(self, df, position):
        return False

    def get_plot_scatters_for_main_graph(self, df) -> list[Scatter]:
        return []

    def get_indicator_graph(self, df):
        return
