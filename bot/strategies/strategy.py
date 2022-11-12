class Strategy:
    def should_long(self):
        return (
            self.is_location_bullish
            and self.is_momentum_bullish
            and self.is_structure_bullish
        )

    def should_short(self):
        return (
            self.is_location_bearish
            and self.is_momentum_bearish
            and self.is_structure_bearish
        )

    def is_location_bullish(self) -> bool:
        # if fibonacci_indicator should long
        # and sma_indicator should long
        pass

    def is_location_bearish(self):
        # LOCATION
        # if fibonacci_indicator should short
        # and sma_indicator should short
        pass

    def is_momentum_bullish(self) -> bool:
        pass

    def is_momentum_bearish(self) -> bool:
        pass

    def is_structure_bullish(self) -> bool:
        pass

    def is_structure_bearish(self) -> bool:
        pass
