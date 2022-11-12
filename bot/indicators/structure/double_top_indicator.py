from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class DoubleTopIndicator(Indicator):
    type = IndicatorType.STRUCTURE

    def set_indicator(self, df):

        pass

    def should_short(self, df) -> bool:
        pass
