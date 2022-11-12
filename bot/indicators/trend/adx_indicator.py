from ta import trend

from bot.helpers.types import IndicatorType
from bot.indicators.indicator import Indicator


class ADXIndicator(Indicator):
    type = IndicatorType.TREND

    def set_indicator(self, df):
        df[("indicators", "ADX")] = trend.ADXIndicator(df.High, df.Low, df.Close)
        return df

    def is_trending(self, df):
        # return true if adx > 25
        # else false
        pass
