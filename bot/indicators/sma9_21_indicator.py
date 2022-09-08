import plotly.graph_objects as go

from bot.indicators.indicator import Indicator
from bot.helpers.utils import get_random_color


class Sma9_21Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA9"] = df["Close"].rolling(9).mean()
        df["SMA21"] = df["Close"].rolling(21).mean()
        df["SMA9>21_trigger"] = df["SMA9"] > df["SMA21"]
        return df

    def should_long(self, df):
        # if trigger was at false and now it at true
        # i.e. SMA9 is going above SMA21
        if not df["SMA9>21_trigger"].iloc[-2] and df["SMA9>21_trigger"].iloc[-1]:
            return True
        return False

    def should_short(self, df):
        # if trigger was at true and now it at false
        # i.e. SMA9 is going under SMA21
        if df["SMA9>21_trigger"].iloc[-2] and not df["SMA9>21_trigger"].iloc[-1]:
            return True
        return False

    def get_plot_scatters(self, df) -> list[go.Scatter]:
        return [
            go.Scatter(
                x=df["CloseDate"],
                y=df["SMA21"],
                name="SMA21",
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
            go.Scatter(
                x=df["CloseDate"],
                y=df["SMA9"],
                name="SMA9",
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
        ]
