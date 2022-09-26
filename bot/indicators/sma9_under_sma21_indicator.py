import plotly.graph_objects as go

from bot.indicators.indicator import Indicator
from bot.helpers.utils import get_random_color


class Sma9_21Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df[("indicators", "SMA9")] = df["Close"].rolling(9).mean()
        df[("indicators", "SMA21")] = df["Close"].rolling(21).mean()
        df[("indicators", "dSMA9")] = (
            df[("indicators", "SMA9")] - df[("indicators", "SMA9")].shift(1)
        ) / (df["CloseTime"] - df["CloseTime"].shift(1))
        df[("indicators", "dSMA21")] = (
            df[("indicators", "SMA21")] - df[("indicators", "SMA21")].shift(1)
        ) / (df["CloseTime"] - df["CloseTime"].shift(1))
        df[("indicators", "SMA9_under_SMA21_trigger")] = (
            df[("indicators", "SMA9")] < df[("indicators", "SMA21")]
        )
        return df

    def should_long(self, df):
        # if trigger was at false and now it at true
        # i.e. SMA9 is going above SMA21
        SMA9_was_under_SMA21 = df[("indicators", "SMA9_under_SMA21_trigger")].iloc[-2]
        SMA9_is_under_SMA21 = df[("indicators", "SMA9_under_SMA21_trigger")].iloc[-1]
        # SMA9_derivative_positive = df["dSMA9"].iloc[-1] > 0
        # SMA9_is_close_to_SMA21 = df["SMA9"].iloc[-1] / df["SMA21"].iloc[-1] > 0.997
        if SMA9_was_under_SMA21 and not SMA9_is_under_SMA21:
            return True
        # if SMA9_was_under_SMA21 and SMA9_derivative_positive and SMA9_is_close_to_SMA21:
        #     return True
        return False

    def should_short(self, df):
        # if trigger was at true and now it at false
        # i.e. SMA9 is going under SMA21
        SMA9_was_under_SMA21 = df[("indicators", "SMA9_under_SMA21_trigger")].iloc[-2]
        SMA9_is_under_SMA21 = df[("indicators", "SMA9_under_SMA21_trigger")].iloc[-1]
        # SMA9_derivative_negative = df["dSMA9"].iloc[-1] < 0
        # SMA21_is_close_to_SMA9 = df["SMA9"].iloc[-1] / df["SMA21"].iloc[-1] < 1.003
        if not SMA9_was_under_SMA21 and SMA9_is_under_SMA21:
            return True
        # if not SMA9_was_under_SMA21 and SMA9_derivative_negative and SMA21_is_close_to_SMA9:
        #     return True
        return False

    def get_plot_scatters_for_main_graph(self, df) -> list[go.Scatter]:
        return [
            go.Scatter(
                x=df["CloseDate"],
                y=df[("indicators", "SMA21")],
                name="SMA21",
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
            go.Scatter(
                x=df["CloseDate"],
                y=df[("indicators", "SMA9")],
                name="SMA9",
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
        ]

    def get_indicator_graph(self, df):
        pass
