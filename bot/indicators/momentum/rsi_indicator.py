import logging

import plotly.express as px
from dash import dcc
from ta import momentum

from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator
from bot.states.states import Position


class RSIIndicator(Indicator):
    type = IndicatorType.MOMENTUM_OSCILLATOR

    def __init__(
        self, rsi_window=14, rsi_long_trigger=30, rsi_short_trigger=70, **kwargs
    ):
        super().__init__(**kwargs)
        self.logger = logging.getLogger(__name__)
        self.rsi_window = rsi_window
        self.rsi_long_trigger = rsi_long_trigger
        self.rsi_short_trigger = rsi_short_trigger

    def set_indicator(self, df):
        df[("indicators", "RSI")] = momentum.rsi(df.Close, window=self.rsi_window)
        df[("indicators", "RSI_oversold_trigger")] = (
            df[("indicators", "RSI")] <= self.rsi_long_trigger
        )
        df[("indicators", "RSI_overbought_trigger")] = (
            df[("indicators", "RSI")] >= self.rsi_short_trigger
        )
        return df

    def should_long(self, df):
        if (
            df[("indicators", "RSI_oversold_trigger")].iloc[-2]
            and not df[("indicators", "RSI_oversold_trigger")].iloc[-1]
        ):
            self.logger.debug(
                f"ShouldLong because RSI was {round(df[('indicators', 'RSI')].iloc[-2], 2)}"
                f" and is now {round(df[('indicators', 'RSI')].iloc[-1], 2)}"
            )
            return True
        return False

    def should_short(self, df):
        if (
            df[("indicators", "RSI_overbought_trigger")].iloc[-2]
            and not df[("indicators", "RSI_overbought_trigger")].iloc[-1]
        ):
            self.logger.debug(
                f"ShouldShort because RSI was {round(df[('indicators', 'RSI')].iloc[-2], 2)}"
                f" and is now {round(df[('indicators', 'RSI')].iloc[-1], 2)}"
            )
            return True
        return False

    def should_quit(self, df, position):
        match position:
            case Position.NONE:
                return False
            case Position.LONG:
                if (
                    not df[("indicators", "RSI_overbought_trigger")].iloc[-2]
                    and df[("indicators", "RSI_overbought_trigger")].iloc[-1]
                ):
                    self.logger.debug(
                        f"ShouldQuit LongPosition because RSI was {round(df[('indicators', 'RSI')].iloc[-2], 2)}"
                        f" and is now {round(df[('indicators', 'RSI')].iloc[-1], 2)}"
                    )
                    return True
                return False
            case Position.SHORT:
                if (
                    not df[("indicators", "RSI_oversold_trigger")].iloc[-2]
                    and df[("indicators", "RSI_oversold_trigger")].iloc[-1]
                ):
                    self.logger.debug(
                        f"ShouldQuit ShortPosition because RSI was {round(df[('indicators', 'RSI')].iloc[-2], 2)}"
                        f" and is now {round(df[('indicators', 'RSI')].iloc[-1], 2)}"
                    )
                    return True
                return False
            case _:
                return False

    def get_plot_scatters_for_main_graph(self, df):
        return []

    def get_indicator_graph(self, df) -> dcc.Graph:
        fig = px.line(
            x=df["CloseDate"],
            y=df[("indicators", "RSI")],
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
            margin={"t": 0, "b": 0},
        )

        return dcc.Graph(
            id="rsi-graph",
            figure=fig,
            style=dict(
                height=150,
            ),
        )
