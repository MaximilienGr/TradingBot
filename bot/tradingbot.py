import logging
from pathlib import Path
from typing import Optional

import pandas as pd
from binance import Client
from pandas import DataFrame

from bot.helpers.utils import (
    get_extremum_between_range,
    interval_to_mili_timestamp,
    merge_candles,
)
from bot.indicators.indicator import Indicator
from bot.states.states import BotState, Position


class TradingBot:
    """
    Main class. This class contains the parameters of the bot: state, market-parameters, dataframe.
    """

    def __init__(
        self,
        start_str: str,
        end_str: str,
        data: Optional[DataFrame] = None,
        symbol: str = "BTCUSDT",
        portfolio: int = 1000,
        interval: str = Client.KLINE_INTERVAL_4HOUR,
        client: Optional[Client] = None,
        indicators: Optional[list[Indicator]] = None,
        stop_limit_percentage: int = 1,
        stop_loss_percentage: float = 0.05,
        refresh_frequency: str = Client.KLINE_INTERVAL_1HOUR,
    ):
        self.current_state = BotState(portfolio=portfolio)
        self.symbol = symbol
        self.interval = interval
        self.start_str = start_str
        self.end_str = end_str
        self.client = client
        self.indicators = indicators or []
        self.stop_limit_percentage = stop_limit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.refresh_frequency = refresh_frequency
        if not data:
            data = self._get_data(
                interval=self.interval, start_str=self.start_str, end_str=self.end_str
            )
        self.df = pd.DataFrame(data)
        self.trades_reporting = pd.DataFrame()
        self.apply_indicators()

    def should_long(self):
        """
        Only one position can be taken per candle.
        If the latest candle already have taken a position, we don't take new positions.
        :return: Boolean to say if we should take a long position
        """
        if self.df.ShortPosition.iloc[-1] or self.df.LongPosition.iloc[-1]:
            return False
        match self.current_state.position:
            case Position.NONE | Position.SHORT:
                return self.df.LongSignal.iloc[-1]
            case Position.LONG:
                return False

    def should_short(self):
        """
        Only one position can be taken per candle.
        If the latest candle already have taken a position, we don't take new positions.
        :return: Boolean to say if we should take a short position
        """
        if self.df.ShortPosition.iloc[-1] or self.df.LongPosition.iloc[-1]:
            return False
        match self.current_state.position:
            case Position.NONE | Position.LONG:
                return self.df.ShortSignal.iloc[-1]
            case Position.SHORT:
                return False

    def should_quit(self):
        """
        If under stoploss, then quit
        If one indicator says should_quit, then quit
        """
        # TODO: Ponderation entre les indicateurs
        _should_quit_indicators = False
        for indicator in self.indicators:
            _should_quit_indicators = (
                indicator.should_quit(df=self.df, position=self.current_state.position)
                or _should_quit_indicators
            )

        return self._protect_funds() or _should_quit_indicators

    def _protect_funds(self):
        """
        Stop the bleeding when it goes not well
        Take profit when it goes very well
        """
        match self.current_state.position:
            case Position.NONE:
                return
            case Position.SHORT:
                # StopLoss to stop bleeding in short positions
                last_short_position_price = self.current_state.price
                stop_loss_activated = self.df.Close.iloc[
                    -1
                ] >= last_short_position_price * (1 + self.stop_loss_percentage)
                stop_limit_activated = self.df.Close.iloc[
                    -1
                ] <= last_short_position_price * (1 - self.stop_limit_percentage)
                # For indicators saying True, if one of the stops is True return False
                if stop_loss_activated or stop_limit_activated:
                    logging.debug(
                        f"StopLoss activated for {self.current_state.position.name} position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
                    )
                    return True
            case Position.LONG:
                # StopLoss to stop bleeding in long positions
                last_long_position_price = self.current_state.price
                stop_loss_activated = self.df.Close.iloc[
                    -1
                ] <= last_long_position_price * (1 - self.stop_loss_percentage)
                stop_limit_activated = self.df.Close.iloc[
                    -1
                ] >= last_long_position_price * (1 + self.stop_limit_percentage)
                # For indicators saying True, if one of the stops is True return False
                if stop_loss_activated or stop_limit_activated:
                    logging.debug(
                        f"StopLoss activated for {self.current_state.position.name} position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})   "
                    )
                    return True
        return False

    def _get_data(self, interval, start_str, end_str):
        """Get all data from binance
        :param start_str : Timestamp to start fetching data from.
        :param end_str: Timestamp to stop fetching data from"""
        try:
            # logging.debug(f"[Fetching data] {pd.Timestamp(start_str * 1000000)} -> {pd.Timestamp(end_str * 1000000)}")

            frame = pd.DataFrame(
                self.client.get_historical_klines(
                    symbol=self.symbol,
                    interval=interval,
                    start_str=start_str,
                    end_str=end_str,
                )
            )
            # Formatting the data
            frame = frame.iloc[:, :7]
            frame.columns = [
                "OpenTime",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume",
                "CloseTime",
            ]
            frame["PositionPrice"] = 0
            frame = frame.astype(float)
            frame[
                [
                    "LongSignal",  # Signal for a Long position
                    "ShortSignal",  # Signal for a Short position
                    "LongPosition",  # When True, means that a long position has been set
                    "ShortPosition",  # When True, means that a short position has been set
                    "QuitPosition",  # When True, means that a position has been quitted
                    "isClosed",  # When True, means that the current candle is closed
                ]
            ] = False
            frame["OpenDate"] = pd.to_datetime(frame["OpenTime"], unit="ms")
            frame["CloseDate"] = pd.to_datetime(frame["CloseTime"], unit="ms")
            return frame
        except Exception as err:
            logging.error(err)

    def update_data(self):
        """
        Update the latest candle.
        If the candle is closed, create a new one.
        If the candle is not closed, get another candle with the size of refresh_frequency,
        and merge it with the latest candle.
        """
        start_str = int(self.df.CloseTime.iloc[-1])
        end_str = start_str + interval_to_mili_timestamp(self.refresh_frequency)
        new_candle = self._get_data(
            interval=self.refresh_frequency, start_str=start_str, end_str=end_str
        )
        # Update of the last candle if it was not closed
        if not self.df.iloc[-1]["isClosed"]:
            old_candle = self.df.tail(1)
            self.df.drop(self.df.tail(1).index, inplace=True)
            new_candle = merge_candles(old_candle=old_candle, new_candle=new_candle)
        self.df = pd.concat([self.df, new_candle], ignore_index=True)
        # Checks on the size of the latest candle
        if self.df.CloseTime.iloc[-1] - self.df.OpenTime.iloc[
            -1
        ] > interval_to_mili_timestamp(self.interval):
            raise Exception(
                "Wtf is this interval ? You are not creating candle correctly :("
            )
        # CloseTime is actually one second before the real close time
        elif (self.df.CloseTime.iloc[-1] + 1) - self.df.OpenTime.iloc[
            -1
        ] == interval_to_mili_timestamp(self.interval):
            self.df.at[self.df.index[-1], "isClosed"] = True

        self.apply_indicators()

    def apply_indicators(self):
        """Make the maths for all indicators"""
        for indicator in self.indicators:
            self.df = indicator.set_indicator(df=self.df)

    def get_indicators_signals(self):
        """Creates two new columns:
        'LongSignal': decision to buy or not.
        'ShortSignal': decision to sell or not.
        All the indicators sending True are needed to buy to have
        """
        # TODO: Ponderation entre les indicateurs
        should_long = True
        for indicator in self.indicators:
            should_long = indicator.should_long(df=self.df) and should_long

        should_short = True
        for indicator in self.indicators:
            should_short = indicator.should_short(df=self.df) and should_short

        self.df.loc[self.df.index[-1], "LongSignal"] = should_long
        self.df.loc[self.df.index[-1], "ShortSignal"] = should_short

    def long(self):
        """
        Take a long position
        :return: None
        """
        if self.current_state.position != Position.NONE:
            raise Exception("Trying to Long while position not quitted properly")

        # TODO: Use the client to go long position
        logging.debug(
            f"Taking LONG position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
        )
        self.df.at[self.df.index[-1], "LongPosition"] = True
        self.df.at[self.df.index[-1], "PositionPrice"] = self.df.Close.iloc[-1]
        self.current_state._update_position(
            new_position=Position.LONG,
            new_time=self.df.CloseDate.iloc[-1],
            new_price=self.df.Close.iloc[-1],
        )

    def short(self):
        """
        Take a short position
        :return: None
        """
        if self.current_state.position != Position.NONE:
            raise Exception("Trying to Long while position not quitted properly")
        # TODO: Use the client to go short position
        logging.debug(
            f"Taking SHORT position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
        )
        self.df.at[self.df.index[-1], "ShortPosition"] = True
        self.df.at[self.df.index[-1], "PositionPrice"] = self.df.Close.iloc[-1]
        self.current_state._update_position(
            new_position=Position.SHORT,
            new_time=self.df.CloseDate.iloc[-1],
            new_price=self.df.Close.iloc[-1],
        )

    def quit_position(self):
        """
        Quit the current position and updates the reporting DataFrame
        :return:
        """
        # TODO: Use the client to quit position
        self.df.loc[self.df.index[-1], "QuitPosition"] = True
        self.df.at[self.df.index[-1], "PositionPrice"] = self.df.Close.iloc[-1]
        self.update_trade_reporting()
        self.current_state._update_position(
            new_position=Position.NONE,
            new_time=self.df.CloseDate.iloc[-1],
            new_price=self.df.Close.iloc[-1],
        )

    def update_trade_reporting(self):
        """
        Add new row to the DataFrame when quitting a position.
        That DataFrame sums up all the trades that have been done.
        """
        # We don't update if there is no position
        if self.current_state.position == Position.NONE:
            return

        current_price = self.df.Close.iloc[-1]
        variation = round(
            self.current_state.get_variation(current_price=current_price) * 100, 3
        )

        # Selecting only indicators
        indicators_columns = self.df[
            [column for column in self.df if type(column) == tuple]
        ]
        indicators_columns.columns = [
            column[1] for column in indicators_columns.columns
        ]

        # Calculation of MaxDrawDown
        (ymin, ymax) = get_extremum_between_range(
            df=self.df,
            x1=self.current_state.time.round(freq="T"),
            x2=self.df.CloseDate.iloc[-1].round(freq="T"),
        )
        max_draw_down = (ymax - ymin) / ymax

        trade_details = pd.DataFrame(
            data={
                "Open": [self.df.Open.iloc[-1]],
                "High": [self.df.High.iloc[-1]],
                "Low": [self.df.Low.iloc[-1]],
                "Close": [self.df.Close.iloc[-1]],
                "Volume": [self.df.Volume.iloc[-1]],
                "EntryTime": [self.current_state.time.round(freq="T")],
                "EntryPrice": [self.current_state.price],
                "Position": [self.current_state.position.name],
                "ExitPrice": [current_price],
                "ExitTime": [self.df.CloseDate.iloc[-1].round(freq="T")],
                "MaxDrawDown": [max_draw_down],
                "Variation": [variation],
                "Portfolio": [self.current_state.portfolio * (1 + variation / 100)],
            }
            | indicators_columns.iloc[-1].to_dict()
        )
        self.trades_reporting = pd.concat(
            [self.trades_reporting, trade_details], ignore_index=True
        )

    def save_trading_reporting_as_csv(self):
        indicators = "-".join([i.__class__.__name__ for i in self.indicators])
        filepath = Path(
            f"./data/trading_history/{indicators}/{self.start_str}-{self.end_str}-{self.interval}-history.csv"
        )
        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.trades_reporting.to_csv(filepath, index=False)
