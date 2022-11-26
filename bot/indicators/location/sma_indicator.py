import logging

import plotly.graph_objects as go

from bot.helpers.types import IndicatorType
from bot.helpers.utils import get_random_color
from bot.indicators.indicator import Indicator
from bot.states.states import Position


class SMAIndicator(Indicator):
    type = IndicatorType.LOCATION

    def __init__(self, value, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.value = value
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df[("indicators", "SMA" + str(self.value))] = (
            df["Close"].rolling(self.value).mean()
        )
        return df

    def should_long(self, df):
        price = df["Close"].iloc[-1]
        price_one_candle_before = df["Close"].iloc[-2]
        sma_value = df[("indicators", "SMA" + str(self.value))].iloc[-1]
        sma_value_one_candle_before = df[("indicators", "SMA" + str(self.value))].iloc[
            -2
        ]
        if price_one_candle_before <= sma_value_one_candle_before and price > sma_value:
            self.logger.debug(
                f"ShouldLong because [SMA: price] was "
                f"[{round(df[('indicators', 'SMA' + str(self.value))].iloc[-2], 2)}: {df['Close'].iloc[-2]}]"
                f" and is now "
                f"[{round(df[('indicators', 'SMA' + str(self.value))].iloc[-1], 2)}: {df['Close'].iloc[-1]}]"
            )
            return True
        return False

    def should_short(self, df):
        price = df["Close"].iloc[-1]
        price_one_candle_before = df["Close"].iloc[-2]
        sma_value = df[("indicators", "SMA" + str(self.value))].iloc[-1]
        sma_value_one_candle_before = df[("indicators", "SMA" + str(self.value))].iloc[
            -2
        ]
        if price_one_candle_before >= sma_value_one_candle_before and price < sma_value:
            self.logger.debug(
                f"ShouldShort because [SMA: price] was "
                f"[{round(df[('indicators', 'SMA' + str(self.value))].iloc[-2], 2)}: {df['Close'].iloc[-2]}]"
                f" and is now "
                f"[{round(df[('indicators', 'SMA' + str(self.value))].iloc[-1], 2)}: {df['Close'].iloc[-1]}]"
            )
            return True
        return False

    def should_quit(self, df, position):
        # On pourrait faire une petite étude statistique :
        # à chaque signal short/long, en moyenne quelle est le plus grand drawndown (et avec quel écart-type)
        match position:
            case Position.LONG if self.should_short(df):
                return True
            case Position.SHORT if self.should_long(df):
                return True
            case Position.NONE | _:
                return False

    def get_plot_scatters_for_main_graph(self, df) -> list[go.Scatter]:
        return [
            go.Scatter(
                x=df["CloseDate"],
                y=df[("indicators", "SMA" + str(self.value))],
                name="SMA" + str(self.value),
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            )
        ]

    def get_indicator_graph(self, df):
        return
