from pandas import DataFrame

from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class IchimokuIndicator(Indicator):
    type = IndicatorType.LOCATION

    def set_indicator(self, df) -> DataFrame:
        # TODO: implement
        return df

    def should_long(self, df) -> bool:
        # TODO: implement
        return False

    def should_short(self, df) -> bool:
        # TODO: implement
        return False
