from bot.client.client import Client


class MockClient(Client):
    def __init__(self, market_data_history=None, **kwargs):
        super().__init__(**kwargs)
        if market_data_history is None:
            market_data_history = []
        self.market_data_history = market_data_history

    def get_historical_klines(self, *args, **kwargs):
        return [self.market_data_history.pop(0)]
