import pandas as pd
from binance import Client
from dash import Output, Input, State, dcc, html, Dash
import plotly.graph_objects as go
from pandas import Timestamp

from bot.helpers.utils import interval_to_mili_timestamp, merge_candles
from bot.states.states import Position, BotState
from bot.indicators.indicator import Indicator
from bot.logging_formatter import logger


class MarketData:
    def __init__(
        self,
        start_str,
        end_str,
        data=None,
        symbol="BTCUSDT",
        portfolio=1000,
        interval=Client.KLINE_INTERVAL_4HOUR,
        lags=5,
        client=None,
        indicators=None,
        stop_limit_percentage=1,
        stop_loss_percentage=0.05,
        refresh_frequency=Client.KLINE_INTERVAL_1HOUR,
    ):
        self._current_state = BotState(portfolio=portfolio)
        self.symbol = symbol
        self.interval = interval
        self.start_str = start_str
        self.end_str = end_str
        self.lags = lags
        self.client = client
        self.indicators: list[Indicator] = indicators
        self.stop_limit_percentage = stop_limit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.refresh_frequency = interval_to_mili_timestamp(refresh_frequency)
        if not data:
            data = self._get_data(start_str=self.start_str, end_str=self.end_str)
        self.df = pd.DataFrame(data)
        self.apply_technicals()

    def get_last_long_position_price(self):
        """Try to get that last long position price."""
        return self.df[self.df["LongSignal"] == 1]["Close"].iloc[-1]

    def get_last_short_position_price(self):
        """Try to get that last short position price."""
        return self.df[self.df["ShortSignal"] == 1]["Close"].iloc[-1]

    def should_long(self):
        match self._current_state.position:
            case Position.NONE | Position.UNDEFINED | Position.SHORT:
                return self.df.LongSignal.iloc[-1]
            case Position.LONG:
                return False

    def should_short(self):
        match self._current_state.position:
            case Position.NONE | Position.UNDEFINED | Position.LONG:
                return self.df.ShortSignal.iloc[-1]
            case Position.SHORT:
                return False

    def protect_funds(self):
        """
        Stop the bleeding when it goes not well
        Take profit when it goes very well
        """
        match self._current_state.position:
            case Position.NONE:
                pass
            case Position.SHORT:
                # StopLoss to stop bleeding in short positions
                last_short_position_price = self.get_last_short_position_price()
                stop_loss_activated = self.df.Close.iloc[
                    -1
                ] >= last_short_position_price * (1 + self.stop_loss_percentage)
                stop_limit_activated = self.df.Close.iloc[
                    -1
                ] <= last_short_position_price * (1 - self.stop_limit_percentage)
                # For indicators saying True, if one of the stops is True return False
                if stop_loss_activated or stop_limit_activated:
                    logger.error(
                        f"Stop activated for {self._current_state.position.name} position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
                    )
                    self.quit_short_position()
            case Position.LONG:
                # StopLoss to stop bleeding in long positions
                last_long_position_price = self.get_last_long_position_price()
                stop_loss_activated = self.df.Close.iloc[
                    -1
                ] <= last_long_position_price * (1 - self.stop_loss_percentage)
                stop_limit_activated = self.df.Close.iloc[
                    -1
                ] >= last_long_position_price * (1 + self.stop_limit_percentage)
                # For indicators saying True, if one of the stops is True return False
                if stop_loss_activated or stop_limit_activated:
                    logger.error(
                        f"Stop activated for {self._current_state.position.name} position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})   "
                    )
                    self.quit_long_position()

    def _get_data(self, start_str, end_str):
        """Get all data from binance
        :param start_str : Timestamp to start fetching data from.
        :param end_str: Timestamp to stop fetching data from"""
        frame = pd.DataFrame(
            self.client.get_historical_klines(
                symbol=self.symbol,
                interval=self.interval,
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
        frame = frame.astype(float)
        frame[
            [
                "LongSignal",  # Signal for a Long position
                "ShortSignal",  # Signal for a Short position
                "LongPosition",  # When True, means that a long position has been set
                "ShortPosition",  # When True, means that a short position has been set
                "QuitPosition",  # When True, means that the current position has been left
                "isClosed",  # When True, means that the current candle is closed
            ]
        ] = False
        frame["OpenDate"] = pd.to_datetime(frame["OpenTime"], unit="ms")
        frame["CloseDate"] = pd.to_datetime(frame["CloseTime"], unit="ms")
        return frame

    def update_data(self):
        """
        Update the latest candle.
        If the candle is closed, create a new one.
        If the candle is not closed, delete the non-closed one, and create a new - updated - one.
        """
        start_str = int(self.df.OpenTime.iloc[-1])
        if self.df.iloc[-1]["isClosed"]:
            end_str = start_str + interval_to_mili_timestamp(self.interval)
        else:
            end_str = int(self.df.CloseTime.iloc[-1]) + self.refresh_frequency
        new_candle = self._get_data(start_str=start_str, end_str=end_str)
        if end_str - start_str > interval_to_mili_timestamp(self.interval):
            raise Exception(
                "Wtf is this interval ? You are not creating candle correctly :("
            )
        elif end_str - start_str == interval_to_mili_timestamp(self.interval):
            new_candle.at[new_candle.index[-1], "isClosed"] = True
        if not self.df.iloc[-1]["isClosed"]:
            old_candle = self.df.tail(1)
            self.df.drop(self.df.tail(1).index, inplace=True)
            new_candle = merge_candles(old_candle=old_candle, new_candle=new_candle)

        self.df = pd.concat([self.df, new_candle], ignore_index=True)

        # Add the rows
        self.df = self.df[~self.df.index.duplicated(keep="first")]
        self.apply_technicals()

    def apply_technicals(self):
        """Make the maths for all indicators"""
        for indicator in self.indicators:
            self.df = indicator.set_indicator(df=self.df)

    def decide(self):
        """Creates two new columns:
        'LongSignal': decision to buy or not.
        'ShortSignal': decision to sell or not.
        All the indicators sending True are needed to buy to have
        """
        should_buy = True
        for indicator in self.indicators:
            should_buy = indicator.should_long(df=self.df) and should_buy

        should_sell = True
        for indicator in self.indicators:
            should_sell = indicator.should_short(df=self.df) and should_sell

        self.df.loc[self.df.index[-1], "LongSignal"] = should_buy
        self.df.loc[self.df.index[-1], "ShortSignal"] = should_sell

    def long(self):
        if self._current_state.position == Position.SHORT:
            self.quit_short_position()
        # TODO: Use the client to go long position
        logger.info(
            f"Taking LONG position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
        )
        self.df.at[self.df.index[-1], "LongPosition"] = True
        self._current_state._update_position(
            new_position=Position.LONG,
            new_time=self.df.CloseDate.iloc[-1],
            new_price=self.df.Close.iloc[-1],
        )

    def short(self):
        if self._current_state.position == Position.LONG:
            self.quit_long_position()
        # TODO: Use the client to go short position
        logger.warning(
            f"Taking SHORT position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
        )
        self.df.at[self.df.index[-1], "ShortPosition"] = True
        self._current_state._update_position(
            new_position=Position.SHORT,
            new_time=self.df.CloseDate.iloc[-1],
            new_price=self.df.Close.iloc[-1],
        )

    def quit_long_position(self):
        # TODO: Use the client to quit long position
        self._current_state._quit_position(
            current_time=self.df.CloseDate.iloc[-1],
            current_price=self.df.Close.iloc[-1],
        )
        self.df.at[self.df.index[-1], "QuitPosition"] = True

    def quit_short_position(self):
        # TODO: Use the client to quit short position
        self._current_state._quit_position(
            current_time=self.df.CloseDate.iloc[-1],
            current_price=self.df.Close.iloc[-1],
        )

    def show_candlestick_with_plotly(self):

        data = [
            go.Candlestick(
                x=self.df["CloseDate"],
                open=self.df["Open"],
                high=self.df["High"],
                low=self.df["Low"],
                close=self.df["Close"],
            ),
            go.Scatter(
                x=self.df["CloseDate"][self.df["LongSignal"] == 1],
                y=self.df["Close"][self.df["LongSignal"] == 1],
                mode="markers",
                marker_symbol="arrow-up",
                marker_size=10,
                marker_color="green",
                name="Long Signal",
            ),
            go.Scatter(
                x=self.df["CloseDate"][self.df["ShortSignal"] == 1],
                y=self.df["Close"][self.df["ShortSignal"] == 1],
                mode="markers",
                marker_symbol="arrow-down",
                marker_size=10,
                marker_color="red",
                name="Short Signal",
            ),
            go.Scatter(
                x=self.df["CloseDate"][self.df["LongPosition"] == 1],
                y=self.df["Close"][self.df["LongPosition"] == 1],
                mode="markers",
                marker_symbol="x",
                marker_size=10,
                marker_color="green",
                name="LongPosition position",
            ),
            go.Scatter(
                x=self.df["CloseDate"][self.df["ShortPosition"] == 1],
                y=self.df["Close"][self.df["ShortPosition"] == 1],
                mode="markers",
                marker_symbol="x",
                marker_size=10,
                marker_color="red",
                name="ShortPosition position",
            ),
        ]
        for i in self.indicators:
            for scatter in i.get_plot_scatters(self.df):
                data.append(scatter)

        graph_candlestick = go.Figure(
            data=data,
            layout=dict(
                hovermode="x", showlegend=True, xaxis=dict(rangeslider_visible=False)
            ),
        )

        ################################################################################################
        # Here to make the vertical scaling automatic when zooming
        ################################################################################################

        app = Dash()

        app.layout = html.Div(
            html.Div(
                [
                    dcc.Graph(
                        id="graph_candlestick",
                        figure=graph_candlestick,
                        style=dict(height=600, width=1300),
                    )
                ]
            )
        )

        # Server side implementation (slow)
        @app.callback(
            Output("graph_candlestick", "figure"),
            [Input("graph_candlestick", "relayoutData")],
            [State("graph_candlestick", "figure")],
        )
        def update_result(relOut, Fig):

            if relOut is None:
                return Fig

            # if you don't use the rangeslider to adjust the plot, then relOut.keys() won't include the key xaxis.range
            elif "xaxis.range[0]" not in relOut.keys():
                newLayout = go.Layout(
                    height=600,
                    width=1300,
                    showlegend=True,
                    xaxis=dict(rangeslider_visible=False),
                    yaxis=dict(autorange=True),
                    hovermode="x",
                    template="plotly",
                )

                Fig["layout"] = newLayout
                return Fig

            else:
                ymin = self.df.loc[
                    self.df["CloseDate"].between(
                        left=Timestamp(relOut["xaxis.range[0]"]),
                        right=Timestamp(relOut["xaxis.range[1]"]),
                        inclusive="neither",
                    ),
                    "Low",
                ].min()
                ymax = self.df.loc[
                    self.df["CloseDate"].between(
                        left=Timestamp(relOut["xaxis.range[0]"]),
                        right=Timestamp(relOut["xaxis.range[1]"]),
                        inclusive="neither",
                    ),
                    "High",
                ].max()

                newLayout = go.Layout(
                    height=600,
                    width=1300,
                    showlegend=True,
                    xaxis=dict(
                        rangeslider_visible=False,
                        range=[
                            Timestamp(relOut["xaxis.range[0]"]),
                            Timestamp(relOut["xaxis.range[1]"]),
                        ],
                    ),
                    yaxis=dict(range=[ymin, ymax]),
                    hovermode="x",
                    template="plotly",
                )

                Fig["layout"] = newLayout
                return Fig

        app.run_server(debug=True, port=1101)
        ################################################################################################
        # graph_candlestick.show()
