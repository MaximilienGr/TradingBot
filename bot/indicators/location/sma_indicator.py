import plotly.graph_objects as go

from bot.helpers.types import IndicatorType
from bot.helpers.utils import get_random_color
from bot.indicators.indicator import Indicator


class SmaIndicator(Indicator):
    type = IndicatorType.LOCATION

    def __init__(self, value, **kwargs):
        self.value = value
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df[("indicators", "SMA" + str(self.value))] = (
            df["Close"].rolling(self.value).mean()
        )
        return df

    def should_long(self, df):
        # return true is_above_sma200
        return True

    def should_short(self, df):
        # return true if is_below_sma200
        return True

    def should_quit(self, df, position):
        return False

    def is_above_sma200(self, df) -> bool:
        if self.value != 200:
            return False
        # return true if price is equal or above sma200
        return False

    def is_below_sma200(self, df) -> bool:
        if self.value != 200:
            return False
        # return true if price is equal or below sma200
        return False

    def get_plot_scatters_for_main_graph(self, df) -> list[go.Scatter]:
        return [
            go.Scatter(
                x=df["CloseDate"],
                y=df[("indicators", "SMA" + str(self.value))],
                name="SMA" + str(self.value),
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            )
        ]

    def get_indicator_graph(self, df):
        return
