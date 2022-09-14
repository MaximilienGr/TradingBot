from ta import momentum
from dash import dcc
import plotly.express as px

from bot.indicators.indicator import Indicator


class RsiIndicator(Indicator):
    def __init__(
        self, rsi_window=14, rsi_long_trigger=30, rsi_short_trigger=70, **kwargs
    ):
        super().__init__(**kwargs)
        self.rsi_window = rsi_window
        self.rsi_long_trigger = rsi_long_trigger
        self.rsi_short_trigger = rsi_short_trigger

    def set_indicator(self, df):
        # TODO: pourquoi les premières valeurs sont à 0 ? Avant c'était des NaN
        df["RSI"] = momentum.rsi(df.Close, window=self.rsi_window)
        return df

    def should_long(self, df):
        return True
        # if df["RSI"].iloc[-1] > self.rsi_buying_trigger:
        #     return True
        # return False

    def should_short(self, df):
        return True
        # if df["RSI"].iloc[-1] > self.rsi_selling_trigger:
        #     return True
        # return False

    def get_plot_scatters_for_main_graph(self, df):
        return []

    def get_indicator_graph(self, df) -> dcc.Graph:
        fig = px.line(
            df,
            x=df["CloseDate"],
            y=df["RSI"],
            title="RSI",
        )

        fig.add_shape(
            type="line",
            x0=df["CloseDate"].iloc[0],
            y0=self.rsi_long_trigger,
            x1=df["CloseDate"].iloc[-1],
            y1=self.rsi_long_trigger,
            line=dict(color="Red", dash="dot"),
            opacity=0.2,
        )
        fig.add_shape(
            type="line",
            x0=df["CloseDate"].iloc[0],
            y0=self.rsi_short_trigger,
            x1=df["CloseDate"].iloc[-1],
            y1=self.rsi_short_trigger,
            line=dict(color="Red", dash="dot"),
            opacity=0.2,
        )
        fig.update_layout(
            yaxis=dict(range=[0, 100]),
            hovermode="x",
        )

        return dcc.Graph(
            id="rsi-graph",
            figure=fig,
            style=dict(
                height=300,
                # width=1300
            ),
        )
