from .indicator import Indicator
import plotly.graph_objects as go


class Sma200Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA200"] = df["Close"].rolling(200).mean()
        return df

    def should_buy(self, df):
        return True

    def should_sell(self, df):
        return True

    def get_plot_scatter(self, df) -> go.Scatter:
        return go.Scatter(
            x=df["Date"],
            y=df["SMA200"],
            name="SMA200",
            line=dict(color="#FFD700"),
            opacity=0.7,
            visible=True,
        )
