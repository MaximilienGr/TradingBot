import logging

import plotly.graph_objects as go
from ta import trend

from bot.helpers.types import IndicatorType
from bot.helpers.utils import get_random_color
from bot.indicators.indicator import Indicator
from bot.indicators.location import SUPPORTED_MA
from bot.states.states import Position


class MAIndicator(Indicator):
    type = IndicatorType.LOCATION

    def __init__(self, ma_type: SUPPORTED_MA, value, **kwargs):
        self.logger = logging.getLogger(__name__)
        self.ma_type = ma_type
        self.value = value
        self.ma_name = self.ma_type + str(value)
        super().__init__(**kwargs)

    def set_indicator(self, df):
        match self.ma_type:
            case "SMA":
                df[("indicators", self.ma_name)] = (
                    df["Close"].rolling(self.value).mean()
                )
            case "EMA":
                df[("indicators", self.ma_name)] = trend.EMAIndicator(
                    df.Close, self.value
                ).ema_indicator()
        self._add_additional_data(df)
        return df

    def _add_additional_data(self, df):
        # This part is about getting derivatives
        df[("indicators", "d" + self.ma_name)] = (
            df[("indicators", self.ma_name)].diff() / df["CloseTime"].diff()
        )
        df[("indicators", "dd" + self.ma_name)] = (
            df[("indicators", "d" + self.ma_name)].diff() / df["CloseTime"].diff()
        )

    def should_long(self, df):
        price = df["Close"].iloc[-1]
        price_one_candle_before = df["Close"].iloc[-2]
        MA_value = df[("indicators", self.ma_name)].iloc[-1]
        MA_value_one_candle_before = df[("indicators", self.ma_name)].iloc[-2]

        if price_one_candle_before <= MA_value_one_candle_before and price > MA_value:
            self.logger.debug(
                f"ShouldLong because [{self.ma_type}: price] was "
                f"[{round(df[('indicators', self.ma_name)].iloc[-2], 2)}: {df['Close'].iloc[-2]}]"
                f" and is now "
                f"[{round(df[('indicators', self.ma_name)].iloc[-1], 2)}: {df['Close'].iloc[-1]}]"
            )
            return True
        return False

    def should_short(self, df):
        price = df["Close"].iloc[-1]
        price_one_candle_before = df["Close"].iloc[-2]
        MA_value = df[("indicators", self.ma_name)].iloc[-1]
        MA_value_one_candle_before = df[("indicators", self.ma_name)].iloc[-2]
        if price_one_candle_before >= MA_value_one_candle_before and price < MA_value:
            self.logger.debug(
                f"ShouldShort because [{self.ma_type}: price] was "
                f"[{round(df[('indicators', self.ma_name)].iloc[-2], 2)}: {df['Close'].iloc[-2]}]"
                f" and is now "
                f"[{round(df[('indicators', self.ma_name)].iloc[-1], 2)}: {df['Close'].iloc[-1]}]"
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
                y=df[("indicators", self.ma_name)],
                name=self.ma_name,
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            )
        ]

    def get_indicator_graph(self, df):
        return
