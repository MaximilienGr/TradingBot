from abc import ABC, abstractmethod

from pandas import DataFrame
from plotly.graph_objects import Scatter


class Indicator(ABC):
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
    def get_plot_scatters(self, df) -> list[Scatter]:
        """
        Returns the Scatter to be added to main graph
        :return: Scatter
        """
        raise NotImplementedError

    # sma = Scatter(
    #     x=self.df.index,
    #     y=self.df["Close"].rolling(i).mean(),  # Pandas SMA
    #     name="SMA" + str(i),
    #     mode="line",
    #     line=dict(color="#3E86AB"),
    #     opacity=0.7,
    #     visible=False,
    # )
