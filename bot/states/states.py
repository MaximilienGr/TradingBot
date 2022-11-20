import logging
from enum import Enum

import pandas as pd
from pydantic import BaseModel


class Position(Enum):
    NONE = 1
    LONG = 2
    SHORT = 3


class BotState(BaseModel):
    """
    position: the curerent position, e.g. short or long
    price: the price when the position was taken
    time: the time when the position was taken
    """

    position: Position = Position.NONE
    price: float | None = None
    time: pd.Timestamp | None = None
    portfolio: float = 0

    def _quit_position(self, current_time, current_price):
        match self.position:
            case Position.NONE:
                return
            case Position.SHORT | Position.LONG:
                logging.debug(
                    f"Quitting {self.position.name} position at {current_price} ({current_time})"
                )
                variation = self.get_variation(current_price)
                self.position = Position.NONE
                self.portfolio *= 1 + variation
                self.price = None
                self.time = None
            case _:
                raise Exception("O_o Wtf is that current state o_O")

    def get_variation(self, current_price):
        match self.position:
            case Position.SHORT:
                return (self.price - current_price) / current_price
            case Position.LONG:
                return (current_price - self.price) / current_price
            case _:
                raise Exception(
                    "O_o Wtf is that current state when trying to get variation o_O"
                )

    def _update_position(
        self, new_position: Position, new_price: float, new_time: pd.Timestamp
    ):
        """When you change position, you'll reset your params and calculate the % of variation"""
        match self.position:
            case Position.SHORT | Position.LONG:
                if new_position != Position.NONE:
                    raise Exception(
                        "O_o Setting a position that has not been quitted properly o_O"
                    )
                else:
                    self._quit_position(new_time, new_price)
                    self.position = new_position
                    self.price = new_price
                    self.time = new_time
            case Position.NONE:
                self.position = new_position
                self.price = new_price
                self.time = new_time
            case _:
                logging.error("O_o Wtf is the current state o_O")
                raise Exception
