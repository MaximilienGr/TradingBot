from abc import ABC, abstractmethod

from pandas import DataFrame


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
    def should_buy(self, df) -> bool:
        """
        Returns True if the indicator is triggering a buy
        :param df: DataFrame that is used to trigger buy according to the current indicator
        :return: bool
        """
        raise NotImplementedError

    @abstractmethod
    def should_sell(self, df) -> bool:
        """
        Returns True if the indicator is triggering a sell
        :param df: DataFrame that is used to trigger sell according to the current indicator
        :return: bool
        """
        raise NotImplementedError
