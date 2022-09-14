import plotly.graph_objects as go

from bot.indicators.indicator import Indicator
from bot.helpers.utils import get_random_color


class SmaIndicator(Indicator):
    def __init__(self, value, **kwargs):
        self.value = value
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA" + str(self.value)] = df["Close"].rolling(self.value).mean()
        return df

    def should_long(self, df):
        return True

    def should_short(self, df):
        return True

    def get_plot_scatters_for_main_graph(self, df) -> list[go.Scatter]:
        return [
            go.Scatter(
                x=df["CloseDate"],
                y=df["SMA" + str(self.value)],
                name="SMA" + str(self.value),
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            )
        ]

    def get_indicator_graph(self, df):
        pass
