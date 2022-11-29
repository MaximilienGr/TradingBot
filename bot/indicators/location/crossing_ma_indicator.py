import logging

import plotly.graph_objects as go
from ta import trend

from bot.helpers.utils import get_random_color
from bot.indicators.indicator import Indicator
from bot.indicators.location import SUPPORTED_MA
from bot.states.states import Position


class CrossingMaIndicator(Indicator):
    def __init__(self, ma_type: SUPPORTED_MA, ma1: int, ma2: int, **kwargs):
        """
        :param ma_type This decides what type of Moving Average will be computed
        :param ma1: This should be the fastest MA
        :param ma2: This should be the slowest MA
        :param kwargs:
        """
        self.ma_type = ma_type
        self.ma1 = ma1
        self.ma2 = ma2
        self.ma1_name = self.ma_type + str(ma1)
        self.ma2_name = self.ma_type + str(ma2)
        self.logger = logging.getLogger(__name__)
        super().__init__(**kwargs)

    def set_indicator(self, df):
        match self.ma_type:
            case "SMA":
                df[("indicators", self.ma1_name)] = df["Close"].rolling(self.ma1).mean()
                df[("indicators", self.ma2_name)] = df["Close"].rolling(self.ma2).mean()
            case "EMA":
                df[("indicators", self.ma1_name)] = trend.EMAIndicator(
                    df.Close, self.ma1
                ).ema_indicator()
                df[("indicators", self.ma2_name)] = trend.EMAIndicator(
                    df.Close, self.ma2
                ).ema_indicator()

        self._add_additional_data(df)
        df[("indicators", self.ma1_name + "_under_MA" + str(self.ma2) + "_trigger")] = (
            df[("indicators", self.ma1_name)] < df[("indicators", self.ma2_name)]
        )
        return df

    def _add_additional_data(self, df):
        # This part is about getting derivatives
        df[("indicators", "d" + self.ma1_name)] = (
            df[("indicators", self.ma1_name)].diff() / df["CloseTime"].diff()
        )
        df[("indicators", "dd" + self.ma1_name)] = (
            df[("indicators", "d" + self.ma1_name)].diff() / df["CloseTime"].diff()
        )

        df[("indicators", "d" + self.ma2_name)] = (
            df[("indicators", self.ma2_name)].diff() / df["CloseTime"].diff()
        )
        df[("indicators", "dd" + self.ma2_name)] = (
            df[("indicators", "d" + self.ma2_name)].diff() / df["CloseTime"].diff()
        )

    def should_long(self, df):
        # i.e. MA1 is going above MA2
        MA1_was_under_MA2 = df[
            ("indicators", self.ma1_name + "_under_MA" + str(self.ma2) + "_trigger")
        ].iloc[-2]
        MA1_is_under_MA2 = df[
            ("indicators", self.ma1_name + "_under_MA" + str(self.ma2) + "_trigger")
        ].iloc[-1]

        # TODO: potential improvement by filtering depending on derivative value
        # MA1_derivative_positive = df["dMA1"].iloc[-1] > 0
        # MA1_is_close_to_MA2 = df["MA1"].iloc[-1] / df["MA2"].iloc[-1] > 0.117
        if MA1_was_under_MA2 and not MA1_is_under_MA2:
            self.logger.debug(
                f"ShouldLong because [MA1: MA2] was "
                f"[{round(df[('indicators', self.ma1_name)].iloc[-2], 2)}: {round(df[('indicators', self.ma2_name)].iloc[-2], 2)}]"
                f" and is now "
                f"[{round(df[('indicators', self.ma1_name)].iloc[-1], 2)}: {round(df[('indicators', self.ma2_name)].iloc[-1], 2)}]"
            )
            return True
        # if MA1_was_under_MA2 and MA1_derivative_positive and MA1_is_close_to_MA2:
        #     return True
        return False

    def should_short(self, df):
        # if trigger was at true and now it at false
        # i.e. MA1 is going under MA2
        MA1_was_under_MA2 = df[
            ("indicators", self.ma1_name + "_under_MA" + str(self.ma2) + "_trigger")
        ].iloc[-2]
        MA1_is_under_MA2 = df[
            ("indicators", self.ma1_name + "_under_MA" + str(self.ma2) + "_trigger")
        ].iloc[-1]
        # MA1_derivative_negative = df["dMA1"].iloc[-1] < 0
        # MA2_is_close_to_MA1 = df["MA1"].iloc[-1] / df["MA2"].iloc[-1] < 1.003
        if not MA1_was_under_MA2 and MA1_is_under_MA2:
            self.logger.debug(
                f"ShouldShort because [MA1: MA2] was "
                f"[{round(df[('indicators', self.ma1_name)].iloc[-2], 2)}: {round(df[('indicators', self.ma2_name)].iloc[-2], 2)}]"
                f" and is now "
                f"[{round(df[('indicators', self.ma1_name)].iloc[-1], 2)}: {round(df[('indicators', self.ma2_name)].iloc[-1], 2)}]"
            )
            return True
        # if not MA1_was_under_MA2 and MA1_derivative_negative and MA2_is_close_to_MA1:
        #     return True
        return False

    def should_quit(self, df, position):
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
                y=df[("indicators", self.ma1_name)],
                name=self.ma1_name,
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
            go.Scatter(
                x=df["CloseDate"],
                y=df[("indicators", self.ma2_name)],
                name=self.ma2_name,
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
        ]

    def get_indicator_graph(self, df):
        return
