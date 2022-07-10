from .indicator import Indicator
import plotly.graph_objects as go


class Sma7Indicator(Indicator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df["SMA7"] = df["Close"].rolling(7).mean()
        return df

    def should_buy(self, df):
        return True

    def should_sell(self, df):
        return True

    def get_plot_scatter(self, df) -> go.Scatter:
        return go.Scatter(
            x=df["Timestamp"],
            y=df["SMA7"],
            name="SMA7",
            line=dict(color="#3E86AB"),
            opacity=0.7,
            visible=True,
        )
