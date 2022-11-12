from pandas import DataFrame

from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class VolumeProfileIndicator(Indicator):
    type = IndicatorType.LOCATION

    def set_indicator(self, df) -> DataFrame:
        # TODO: implement
        return df

    def should_long(self, df) -> bool:
        # TODO: implement
        # if market is trending down and self.is_on_high_volume_node
        # return true
        return self.is_in_low_value_area(df)

    def should_short(self, df) -> bool:
        # TODO: implement
        # if market is trending up and self.is_on_high_volume_node
        # return true
        return self.is_in_high_value_are(df)

    def is_in_high_value_are(self, df) -> bool:
        return False

    def is_in_low_value_area(self, df) -> bool:
        return False

    def is_on_high_volume_node(self, df) -> bool:
        # return true if price 10% below or above HVN
        return False
