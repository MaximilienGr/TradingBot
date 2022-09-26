import numpy as np
import pandas as pd
from ta import momentum
from plotly.graph_objs import Scatter

from bot.indicators.indicator import Indicator


class StochasticIndicator(Indicator):
    def __init__(self, lags, stoch_window, stoch_smooth_window, stoch_limits, **kwargs):
        super().__init__(**kwargs)
        self.lags = lags
        self.stoch_window = stoch_window
        self.stoch_smooth_window = stoch_smooth_window
        self.stoch_limits = stoch_limits

    def set_indicator(self, df):
        # What is smooth window ?
        df["%K"] = momentum.stoch(
            df.High,
            df.Low,
            df.Close,
            window=self.stoch_window,
            smooth_window=0,
        )

        # Buying signals:
        # - %K crosses %D upwards
        # - %K crosses 20% upwards
        # Selling signals:
        # - %K crosses %D downwards
        # - %K crosses 80% downwards

        df["%D"] = df["%K"].rolling(self.stoch_smooth_window).mean()
        # "stoch_buying_trigger" is True when %K is below 20%.
        df["stoch_buying_trigger"] = np.where(
            self.get_stoch_trigger(df=df, type="buying"), 1, 0
        )
        # "stoch_selling_trigger" is True when %K is above 80%.
        df["stoch_selling_trigger"] = np.where(
            self.get_stoch_trigger(df=df, type="selling"), 1, 0
        )
        # "stoch_cross_trigger" is True when %K is below %D.
        df["stoch_cross_trigger"] = np.where(self.get_stoch_cross_trigger(df=df), 1, 0)
        return df

    def get_stoch_trigger(self, df, type):
        """Shifts `self.lags` times the stochastic indicator for each dates.
        Each dates has `self.lags` bools, if one of them is True then is it seen as a trigger"""
        if type == "buying":
            masks = [
                (df["%K"].shift(i) < self.stoch_limits[0])
                & (df["%D"].shift(i) < self.stoch_limits[0])
                for i in range(self.lags + 1)
            ]
        else:
            masks = [
                (df["%K"].shift(i) > self.stoch_limits[1])
                & (df["%D"].shift(i) > self.stoch_limits[1])
                for i in range(self.lags + 1)
            ]
        return pd.DataFrame(masks).sum(axis=0)

    def get_stoch_cross_trigger(self, df):
        """Shifts `self.lags` times the stochastic indicator for each dates.
        Each dates has `self.lags` bools, if one of them is True then is it seen as a trigger"""
        masks = [(df["%K"].shift(i) < df["%D"].shift(i)) for i in range(self.lags + 1)]
        return pd.DataFrame(masks).sum(axis=0)

    def should_long(self, df):
        stoch_trigger_indicator = (
            df["stoch_selling_trigger"]
            & df["%K"].between(self.stoch_limits[0], self.stoch_limits[1])
            & df["%D"].between(self.stoch_limits[0], self.stoch_limits[1])
        )

        stoch_cross_trigger_indicator = df["stoch_cross_trigger"] & (
            df["%K"] > df["%D"]
        )
        # il faut voir si on récupère bien la dernière ligne seulement
        return (stoch_trigger_indicator | stoch_cross_trigger_indicator)[-1]

    def should_short(self, df):

        # TODO: ca renvoit toujours False... Pourquoi ?
        stoch_trigger_indicator = (
            df["stoch_buying_trigger"]
            & df["%K"].between(self.stoch_limits[0], self.stoch_limits[1])
            & df["%D"].between(self.stoch_limits[0], self.stoch_limits[1])
        )

        stoch_cross_trigger_indicator = ~df["stoch_cross_trigger"] & (
            df["%K"] < df["%D"]
        )
        return (stoch_trigger_indicator | stoch_cross_trigger_indicator)[-1]

    def get_plot_scatters_for_main_graph(self, df) -> list[Scatter]:
        return []

    def get_indicator_graph(self, df):
        pass
