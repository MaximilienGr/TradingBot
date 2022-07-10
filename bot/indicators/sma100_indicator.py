from .indicator import Indicator
import plotly.graph_objects as go


class Sma100Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA100"] = df["Close"].rolling(100).mean()
        return df

    def should_buy(self, df):
        return True

    def should_sell(self, df):
        return True

    def get_plot_scatter(self, df) -> go.Scatter:
        return go.Scatter(
            x=df["Date"],
            y=df["SMA100"],
            name="SMA100",
            line=dict(color="#5D814E"),
            opacity=0.7,
            visible=True,
        )
