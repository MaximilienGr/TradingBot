from .indicator import Indicator
import plotly.graph_objects as go


class Sma20Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA20"] = df["Close"].rolling(20).mean()
        return df

    def should_buy(self, df):
        return True

    def should_sell(self, df):
        return True

    def get_plot_scatter(self, df) -> go.Scatter:
        return go.Scatter(
            x=df["Date"],
            y=df["SMA20"],
            name="SMA20",
            line=dict(color="#3E86AB"),
            opacity=0.7,
            visible=True,
        )
