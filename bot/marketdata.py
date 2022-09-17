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
        match self._current_state.position:
            case Position.NONE | Position.UNDEFINED | Position.SHORT:
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
                last_short_position_price = self._current_state.price
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
                    self.quit_position()
            case Position.LONG:
                # StopLoss to stop bleeding in long positions
                last_long_position_price = self._current_state.price
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
                    self.quit_position()

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
        frame["PositionPrice"] = 0
        frame = frame.astype(float)
        frame[
            [
                "LongSignal",  # Signal for a Long position
                "ShortSignal",  # Signal for a Short position
                "LongPosition",  # When True, means that a long position has been set
                "ShortPosition",  # When True, means that a short position has been set
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
        If the candle is not closed, get another candle with the size of refresh_frequency,
        and merge it with the latest candle.
        """
        start_str = int(self.df.CloseTime.iloc[-1])
        end_str = start_str + self.refresh_frequency
        new_candle = self._get_data(start_str=start_str, end_str=end_str)
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
        should_buy = True
        for indicator in self.indicators:
            should_buy = indicator.should_long(df=self.df) and should_buy

        should_sell = True
        for indicator in self.indicators:
            should_sell = indicator.should_short(df=self.df) and should_sell

        self.df.loc[self.df.index[-1], "LongSignal"] = should_buy
        self.df.loc[self.df.index[-1], "ShortSignal"] = should_sell

    def long(self):
        """
        Take a long position
        :return: None
        """
        if self._current_state.position == Position.SHORT:
            self.quit_position()
        # TODO: Use the client to go long position
        logger.info(
            f"Taking LONG position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
        )
        self.df.at[self.df.index[-1], "LongPosition"] = True
        self.df.at[self.df.index[-1], "PositionPrice"] = self.df.Close.iloc[-1]
        self._current_state._update_position(
            new_position=Position.LONG,
            new_time=self.df.CloseDate.iloc[-1],
            new_price=self.df.Close.iloc[-1],
        )

    def short(self):
        """
        Take a short position
        :return: None
        """
        if self._current_state.position == Position.LONG:
            self.quit_position()
        # TODO: Use the client to go short position
        logger.warning(
            f"Taking SHORT position at {self.df.Close.iloc[-1]} ({self.df.CloseDate.iloc[-1]})"
        )
        self.df.at[self.df.index[-1], "ShortPosition"] = True
        self.df.at[self.df.index[-1], "PositionPrice"] = self.df.Close.iloc[-1]
        self._current_state._update_position(
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
        self.update_trade_reporting()
        self._current_state._quit_position(
            current_time=self.df.CloseDate.iloc[-1],
            current_price=self.df.Close.iloc[-1],
        )

    def update_trade_reporting(self):
        """
        Add new row to the DataFrame when quitting a position.
        That DataFrame sums up all the trades that have been done.
        """
        # TODO: Mettre plusieurs niveau dans les noms de colonnes (par ex: taking position/ quitting position)
        # avec ces niveau on peut avoir les datas des moments de prises de position pour pouvoir faire du ML dessus ??
        # Et ca permet aussi d'avoir une premiere étape pour analyser pourquoi les calls étaient mauvais ?
        # Comme ca ensuite on peut mieux filter et avoir de meilleurs signaux de prise de position
        current_price = self.df.Close.iloc[-1]
        variation = round(
            self._current_state.get_variation(current_price=current_price) * 100, 3
        )
        trade_details = pd.DataFrame(
            data={
                "EntryTime": [self._current_state.time],
                "EntryPrice": [self._current_state.price],
                "Position": [self._current_state.position.name],
                "ExitPrice": [current_price],
                "ExitTime": [self.df.CloseDate.iloc[-1]],
                "Variation": [variation],
                "Portfolio": [self._current_state.portfolio],
            }
        )
        self.trades_reporting = pd.concat(
            [self.trades_reporting, trade_details], ignore_index=True
        )

    def _get_extremum_between_range(self, x1, x2):
        ymin = self.df.loc[
            self.df["CloseDate"].between(
                left=Timestamp(x1),
                right=Timestamp(x2),
                inclusive="neither",
            ),
            "Low",
        ].min()
        ymax = self.df.loc[
            self.df["CloseDate"].between(
                left=Timestamp(x1),
                right=Timestamp(x2),
                inclusive="neither",
            ),
            "High",
        ].max()
        return [ymin, ymax]

    def setup_dash(self) -> Dash:
        legend = dict(xanchor="left", yanchor="top", orientation="h", y=0.99, x=0.01)
        data = [
            # Candlesticks
            go.Candlestick(
                x=self.df["CloseDate"],
                open=self.df["Open"],
                high=self.df["High"],
                low=self.df["Low"],
                close=self.df["Close"],
            ),
            # Green arrow up located at (time, price) for long signals
            go.Scatter(
                x=self.df["CloseDate"][self.df["LongSignal"] == 1],
                y=self.df["Close"][self.df["LongSignal"] == 1],
                mode="markers",
                marker_symbol="arrow-up",
                marker_size=10,
                marker_color="green",
                name="Long Signal",
            ),
            # Red arrow down located at (time, price) for short signals
            go.Scatter(
                x=self.df["CloseDate"][self.df["ShortSignal"] == 1],
                y=self.df["Close"][self.df["ShortSignal"] == 1],
                mode="markers",
                marker_symbol="arrow-down",
                marker_size=10,
                marker_color="red",
                name="Short Signal",
            ),
            # Green cross located at (time, price) for long positions
            go.Scatter(
                x=self.df["CloseDate"][self.df["LongPosition"] == 1],
                y=self.df["PositionPrice"][self.df["LongPosition"] == 1],
                mode="markers",
                marker_symbol="x",
                marker_size=10,
                marker_color="green",
                name="LongPosition position",
            ),
            # Red cross located at (time, price) for short positions
            go.Scatter(
                x=self.df["CloseDate"][self.df["ShortPosition"] == 1],
                y=self.df["PositionPrice"][self.df["ShortPosition"] == 1],
                mode="markers",
                marker_symbol="x",
                marker_size=10,
                marker_color="red",
                name="ShortPosition position",
            ),
        ]
        childrens_graphs = []
        for i in self.indicators:
            # Adding the data of each indicator in the main graph
            for scatter in i.get_plot_scatters_for_main_graph(self.df):
                data.append(scatter)
            # Adding each indicator's plot in the dashboard
            if (indicator_graph := i.get_indicator_graph(self.df)) is not None:
                childrens_graphs.append(indicator_graph)

        graph_candlestick = go.Figure(
            data=data,
            layout=dict(
                hovermode="x",
                xaxis=dict(rangeslider_visible=False),
                yaxis=dict(autorange=True),
                legend=legend,
                margin={"t": 0, "b": 0},
            ),
        )

        ################################################################################################
        #                    Here to make the vertical scaling automatic when zooming                  #
        ################################################################################################

        app = Dash()

        app.layout = html.Div(
            html.Div(
                children=[
                    dcc.Graph(
                        id="graph_candlestick",
                        figure=graph_candlestick,
                        style=dict(
                            height=500,
                        ),
                    )
                ]
                + childrens_graphs
            )
        )

        childrens_graphs_State = [State(plot.id, "figure") for plot in childrens_graphs]
        childrens_graphs_Output = [
            Output(plot.id, "figure") for plot in childrens_graphs
        ]

        # Server side implementation (slow)
        @app.callback(
            [Output("graph_candlestick", "figure")] + childrens_graphs_Output,
            Input("graph_candlestick", "relayoutData"),
            [State("graph_candlestick", "figure")] + childrens_graphs_State,
        )
        def update_result(relOut, Fig, *my_args):
            if relOut is None:
                return Fig, *my_args
            # if you don't use the rangeslider to adjust the plot, then relOut.keys() won't include the key xaxis.range
            elif "xaxis.range[0]" in relOut.keys():
                Fig["layout"]["yaxis"]["range"] = self._get_extremum_between_range(
                    x1=Timestamp(relOut["xaxis.range[0]"]),
                    x2=Timestamp(relOut["xaxis.range[1]"]),
                )
                Fig["layout"]["yaxis"]["autorange"] = False
                for plot in my_args:
                    plot["layout"]["xaxis"]["autorange"] = False
                    plot["layout"]["xaxis"]["range"] = [
                        relOut["xaxis.range[0]"],
                        relOut["xaxis.range[1]"],
                    ]
                return Fig, *my_args
            else:
                return Fig, *my_args

        app.run_server(port=1101)
        ################################################################################################
