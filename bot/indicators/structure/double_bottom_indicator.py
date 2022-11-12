from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class DoubleBottomIndicator(Indicator):
    type = IndicatorType.STRUCTURE

    def set_indicator(self, df):
        return

    def should_long(self, df) -> bool:
        return False
