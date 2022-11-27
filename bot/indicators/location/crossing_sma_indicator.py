import logging

import plotly.graph_objects as go

from bot.helpers.utils import get_random_color
from bot.indicators.indicator import Indicator
from bot.states.states import Position


class CrossingSmaIndicator(Indicator):
    def __init__(self, sma1, sma2, **kwargs):
        """
        :param sma1: This should be the fastest SMA
        :param sma2: This should be the slowest SMA
        :param kwargs:
        """
        self.sma1 = sma1
        self.sma2 = sma2
        self.sma1_name = "SMA" + str(sma1)
        self.sma2_name = "SMA" + str(sma2)
        self.logger = logging.getLogger(__name__)
        super().__init__(**kwargs)

    def set_indicator(self, df):
        df[("indicators", self.sma1_name)] = df["Close"].rolling(self.sma1).mean()
        df[("indicators", self.sma2_name)] = df["Close"].rolling(self.sma2).mean()

        # This part is about getting derivatives
        df[("indicators", "d" + self.sma1_name)] = (
            df[("indicators", self.sma1_name)].diff() / df["CloseTime"].diff()
        )
        df[("indicators", "dd" + self.sma1_name)] = (
            df[("indicators", "d" + self.sma1_name)].diff() / df["CloseTime"].diff()
        )

        df[("indicators", "d" + self.sma2_name)] = (
            df[("indicators", self.sma2_name)].diff() / df["CloseTime"].diff()
        )
        df[("indicators", "dd" + self.sma2_name)] = (
            df[("indicators", "d" + self.sma2_name)].diff() / df["CloseTime"].diff()
        )

        df[
            ("indicators", self.sma1_name + "_under_SMA" + str(self.sma2) + "_trigger")
        ] = (df[("indicators", self.sma1_name)] < df[("indicators", self.sma2_name)])
        return df

    def should_long(self, df):
        # i.e. SMA1 is going above SMA2
        SMA1_was_under_SMA2 = df[
            ("indicators", self.sma1_name + "_under_SMA" + str(self.sma2) + "_trigger")
        ].iloc[-2]
        SMA1_is_under_SMA2 = df[
            ("indicators", self.sma1_name + "_under_SMA" + str(self.sma2) + "_trigger")
        ].iloc[-1]

        # TODO: potential improvment by filtering depending on derivative value
        # SMA1_derivative_positive = df["dSMA1"].iloc[-1] > 0
        # SMA1_is_close_to_SMA2 = df["SMA1"].iloc[-1] / df["SMA2"].iloc[-1] > 0.117
        if SMA1_was_under_SMA2 and not SMA1_is_under_SMA2:
            self.logger.debug(
                f"ShouldLong because [SMA1: SMA2] was "
                f"[{round(df[('indicators', self.sma1_name)].iloc[-2], 2)}: {round(df[('indicators', self.sma2_name)].iloc[-2], 2)}]"
                f" and is now "
                f"[{round(df[('indicators', self.sma1_name)].iloc[-1], 2)}: {round(df[('indicators', self.sma2_name)].iloc[-1], 2)}]"
            )
            return True
        # if SMA1_was_under_SMA2 and SMA1_derivative_positive and SMA1_is_close_to_SMA2:
        #     return True
        return False

    def should_short(self, df):
        # if trigger was at true and now it at false
        # i.e. SMA1 is going under SMA2
        SMA1_was_under_SMA2 = df[
            ("indicators", self.sma1_name + "_under_SMA" + str(self.sma2) + "_trigger")
        ].iloc[-2]
        SMA1_is_under_SMA2 = df[
            ("indicators", self.sma1_name + "_under_SMA" + str(self.sma2) + "_trigger")
        ].iloc[-1]
        # SMA1_derivative_negative = df["dSMA1"].iloc[-1] < 0
        # SMA2_is_close_to_SMA1 = df["SMA1"].iloc[-1] / df["SMA2"].iloc[-1] < 1.003
        if not SMA1_was_under_SMA2 and SMA1_is_under_SMA2:
            self.logger.debug(
                f"ShouldShort because [SMA1: SMA2] was "
                f"[{round(df[('indicators', self.sma1_name)].iloc[-2], 2)}: {round(df[('indicators', self.sma2_name)].iloc[-2], 2)}]"
                f" and is now "
                f"[{round(df[('indicators', self.sma1_name)].iloc[-1], 2)}: {round(df[('indicators', self.sma2_name)].iloc[-1], 2)}]"
            )
            return True
        # if not SMA1_was_under_SMA2 and SMA1_derivative_negative and SMA2_is_close_to_SMA1:
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
                y=df[("indicators", self.sma1_name)],
                name=self.sma1_name,
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
            go.Scatter(
                x=df["CloseDate"],
                y=df[("indicators", self.sma2_name)],
                name=self.sma2_name,
                line=dict(color=get_random_color()),
                opacity=0.7,
                visible=True,
            ),
        ]

    def get_indicator_graph(self, df):
        return
