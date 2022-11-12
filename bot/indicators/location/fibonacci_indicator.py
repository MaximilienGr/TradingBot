from pandas import DataFrame

from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class FibonacciIndicator(Indicator):
    type = IndicatorType.LOCATION
    ratios = (0.382, 0.618, 0.7, 1, 1.618, 2)

    def set_indicator(self, df) -> DataFrame:
        # TODO: implement
        # calc most recent high and low peak
        # for each ratio, calc corresponding price level
        return df

    @property
    def levels(self) -> tuple:
        # TODO: implement
        return tuple()

    def should_long(self, df) -> bool:
        # TODO: implement
        # if down trend:
        # if self.is_in_reload_zone
        # or if self.is_in_garage_zone
        # return true
        return False

    def should_short(self, df) -> bool:
        # TODO: implement
        # if up trend:
        # if self.is_in_reload_zone
        # or if self.is_in_garage_zone
        # return true
        return False

    def should_quit(self, df, position) -> bool:
        # return true if price crosses level 1, 5 or 6
        return False

    def is_in_ranging_zone(self, df) -> bool:
        # TODO: implement
        # return true if price is between level 1 and 2
        return False

    def is_in_reload_zone(self, df) -> bool:
        # TODO: implement
        # return true if price is between level 2 and 3
        return False

    def is_in_garage_zone(self, df) -> bool:
        # TODO: implement
        # return true if price is between level 2 and 3
        return False
