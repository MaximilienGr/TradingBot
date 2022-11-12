from abc import ABC, abstractmethod

from dash import dcc
from pandas import DataFrame
from plotly.graph_objects import Scatter

from bot.helpers.types import IndicatorType


class Indicator(ABC):
    type: IndicatorType | None = None

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @abstractmethod
    def set_indicator(self, df) -> DataFrame:
        """
        This method adds new columns that are only focusing on one indicator
        :param df: DataFrame that will be updated once the indicator is set
        :return: DataFrame
        """
        raise NotImplementedError

    @abstractmethod
    def should_long(self, df) -> bool:
        """
        Returns True if the indicator is triggering a buy
        :param df: DataFrame that is used to trigger buy according to the current indicator
        :return: bool
        """
        raise NotImplementedError

    @abstractmethod
    def should_short(self, df) -> bool:
        """
        Returns True if the indicator is triggering a sell
        :param df: DataFrame that is used to trigger sell according to the current indicator
        :return: bool
        """
        raise NotImplementedError

    @abstractmethod
    def should_quit(self, df, position) -> bool:
        """
        Returns True if the indicator says conditions are bad to be in market
        :param position:
        :param df: DataFrame that is used to trigger sell according to the current indicator
        :return: bool
        """
        raise NotImplementedError

    @abstractmethod
    def get_plot_scatters_for_main_graph(self, df) -> list[Scatter]:
        """
        Returns the Scatter to be added to main graph
        :return: Scatter
        """
        raise NotImplementedError

    @abstractmethod
    def get_indicator_graph(self, df) -> dcc.Graph:
        """
        Returns the graph that is specific to indicator. This one will be added in the final dashboard.
        :return: dcc.Graph
        """
        raise NotImplementedError
