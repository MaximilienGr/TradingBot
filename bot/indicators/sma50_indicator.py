from .indicator import Indicator
import plotly.graph_objects as go


class Sma50Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA50"] = df["Close"].rolling(50).mean()
        return df

    def should_buy(self, df):
        return True

    def should_sell(self, df):
        return True

    def get_plot_scatter(self, df) -> go.Scatter:
        return go.Scatter(
            x=df["Date"],
            y=df["SMA50"],
            name="SMA50",
            line=dict(color="#F47174"),
            opacity=0.7,
            visible=True,
        )
