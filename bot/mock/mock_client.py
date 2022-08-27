class MockClient:
    def __init__(self, market_data_history=None):
        if market_data_history is None:
            market_data_history = []
        self.market_data_history = market_data_history

    def get_historical_klines(self, *args, **kwargs):
        return [self.market_data_history.pop(0)]
