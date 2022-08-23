import numpy as np
import pandas as pd
from binance import Client
from dash import Output, Input, State, dcc, html, Dash
import plotly.graph_objects as go
from pandas import Timestamp

from bot.indicators.indicator import Indicator


class MarketData:
    def __init__(
        self,
        start_str,
        end_str,
        data=None,
        symbol="BTCUSDT",
        interval=Client.KLINE_INTERVAL_1MINUTE,
        lags=5,
        client=None,
        indicators=None,
        stop_limit_percentage=0.999,
        stop_loss_percentage=1.005,
        stoch_window=14,
        stoch_smooth_window=3,
        stoch_trigger=20,
        stoch_limits=[20, 80],
    ):
        self.symbol = symbol
        self.interval = interval
        self.start_str = start_str
        self.end_str = end_str
        self.lags = lags
        self.client = client
        self.indicators: list[Indicator] = indicators
        self.stop_limit_percentage = stop_limit_percentage
        self.stop_loss_percentage = stop_loss_percentage
        self.stoch_window = stoch_window
        self.stoch_smooth_window = stoch_smooth_window
        self.stoch_trigger = stoch_trigger
        self.stoch_limits = stoch_limits
        if not data:
            data = self._get_data(start_str=self.start_str, end_str=self.end_str)
        self.df = pd.DataFrame(data)
        self.apply_technicals()

    def should_buy(self):
        return bool(self.df.Buy.iloc[-1])

    def should_sell(self, buy_price):
        indicators_decision = bool(self.df.Sell.iloc[-1])
        stop_loss_activated = self.df.Close[-1] <= buy_price * self.stop_loss_percentage
        stop_limit_activated = (
            self.df.Close[-1] >= buy_price * self.stop_limit_percentage
        )
        return stop_loss_activated or stop_limit_activated or indicators_decision

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
        frame = frame.iloc[:, :6]
        frame.columns = ["Time", "Open", "High", "Low", "Close", "Volume"]
        frame["Timestamp"] = frame["Time"]
        frame[["Buy", "Bought", "Sell", "Sold"]] = 0
        frame = frame.set_index("Time")
        frame.index = pd.to_datetime(frame.index, unit="ms")
        frame = frame.astype(float)
        frame["Date"] = pd.to_datetime(frame["Timestamp"], unit="ms")
        return frame

    def update_data(self):
        """Get the new line for the latest candle, concatenate it with the rest and apply_technicals to it"""
        # TODO: Là on recalcule toutes les lignes à chaque update; il faut faire plus intelligemment
        start_str = int(self.df.Timestamp[-1])
        # end_str is on interval after start_str
        end_str = int(start_str * 2 - self.df.Timestamp[-2])
        new_candle = self._get_data(start_str=start_str, end_str=end_str)
        # reset indexes to ease the adding of the new row
        df = self.df.reset_index()
        new_candle = new_candle.reset_index()
        # Add the rows
        df = pd.concat([df, new_candle], ignore_index=True)
        # set back index
        self.df = df.set_index("Time")
        self.df = self.df[~self.df.index.duplicated(keep="first")]
        self.apply_technicals()

    def apply_technicals(self):
        """Make the maths for all indicators"""
        for indicator in self.indicators:
            self.df = indicator.set_indicator(df=self.df)

    def decide(self):
        """Creates two new columns:
        'Buy': decision to buy or not.
        'Sell': decision to sell or not.
        Is needed to buy to have all the indicators sending True
        """
        should_buy = True
        for indicator in self.indicators:
            should_buy = indicator.should_buy(df=self.df) and should_buy

        should_sell = True
        for indicator in self.indicators:
            should_sell = indicator.should_sell(df=self.df) and should_sell

        self.df["Buy"] = should_buy
        self.df["Sell"] = should_sell

    def show_candlestick_with_plotly(self):

        data = [
            go.Candlestick(
                x=self.df["Date"],
                open=self.df["Open"],
                high=self.df["High"],
                low=self.df["Low"],
                close=self.df["Close"],
            ),
            go.Scatter(
                x=self.df["Date"][self.df["Bought"] == 1],
                y=self.df["Open"][self.df["Bought"] == 1],
                mode="markers",
                marker_symbol="arrow-up",
                marker_size=10,
                marker_color="green",
                name="Buying position",
            ),
            go.Scatter(
                x=self.df["Date"][self.df["Sold"] == 1],
                y=self.df["Open"][self.df["Sold"] == 1],
                mode="markers",
                marker_symbol="arrow-down",
                marker_size=10,
                marker_color="red",
                name="Selling position",
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
                    self.df["Date"].between(
                        left=Timestamp(relOut["xaxis.range[0]"]),
                        right=Timestamp(relOut["xaxis.range[1]"]),
                        inclusive="neither",
                    ),
                    "Low",
                ].min()
                ymax = self.df.loc[
                    self.df["Date"].between(
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
