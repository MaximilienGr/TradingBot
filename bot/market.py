from bot.indicators.trend.adx_indicator import ADXIndicator


class Market:
    adx = ADXIndicator()

    @property
    def is_bullish(self):
        # TODO; implement
        # if series of higher highs
        # and if adx > 25 of if price is above sma200
        # return true
        return False

    @property
    def is_bearish(self):
        # TODO; implement
        # if series of lower lows
        # and if adx > 25 or if price is below sma200
        # return true
        return False

    @property
    def is_ranging(self):
        # TODO; implement
        # if adx < 25
        # if price in fibo ranging zone and is going in the opposite direction of last trend
        # return true
        return False
