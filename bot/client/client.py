from abc import abstractmethod, ABC


class Client(ABC):
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    @abstractmethod
    def get_historical_klines(self, symbol, interval, start_str, end_str) -> list:
        """
        Get Historical Klines from the specific client
        :param symbol: Name of symbol pair e.g BNBBTC
        :type symbol: str
        :param interval: Binance Kline interval
        :type interval: str
        :param start_str: optional - start date string in UTC format or timestamp in milliseconds
        :type start_str: str|int
        :param end_str: optional - end date string in UTC format or timestamp in milliseconds (default will fetch everything up to now)
        :type end_str: str|int

         :return: list of OHLCV values (Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore)
        """
        raise NotImplementedError
