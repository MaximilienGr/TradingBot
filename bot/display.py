import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
from pandas import Timestamp

from bot.helpers.utils import get_extremum_between_range
from bot.tradingbot import TradingBot


def setup_dash(trading_bot: TradingBot):
    legend = dict(xanchor="left", yanchor="top", orientation="h", y=0.99, x=0.01)
    trading_reporting_columns = [
        "EntryTime",
        "EntryPrice",
        "Position",
        "ExitPrice",
        "ExitTime",
        "MaxDrawDown",
        "Variation",
        "Portfolio",
    ]
    data = [
        # Candlesticks
        go.Candlestick(
            x=trading_bot.df["CloseDate"],
            open=trading_bot.df["Open"],
            high=trading_bot.df["High"],
            low=trading_bot.df["Low"],
            close=trading_bot.df["Close"],
        ),
        # Green arrow up located at (time, price) for long signals
        go.Scatter(
            x=trading_bot.df["CloseDate"][trading_bot.df["LongSignal"] == 1],
            y=trading_bot.df["Close"][trading_bot.df["LongSignal"] == 1],
            mode="markers",
            marker_symbol="arrow-up",
            marker_size=10,
            marker_color="green",
            name="Long Signal",
        ),
        # Red arrow down located at (time, price) for short signals
        go.Scatter(
            x=trading_bot.df["CloseDate"][trading_bot.df["ShortSignal"] == 1],
            y=trading_bot.df["Close"][trading_bot.df["ShortSignal"] == 1],
            mode="markers",
            marker_symbol="arrow-down",
            marker_size=10,
            marker_color="red",
            name="Short Signal",
        ),
        # Green cross located at (time, price) for long positions
        go.Scatter(
            x=trading_bot.df["CloseDate"][trading_bot.df["LongPosition"] == 1],
            y=trading_bot.df["PositionPrice"][trading_bot.df["LongPosition"] == 1],
            mode="markers",
            marker_symbol="x",
            marker_size=10,
            marker_color="green",
            name="LongPosition position",
        ),
        # Red cross located at (time, price) for short positions
        go.Scatter(
            x=trading_bot.df["CloseDate"][trading_bot.df["ShortPosition"] == 1],
            y=trading_bot.df["PositionPrice"][trading_bot.df["ShortPosition"] == 1],
            mode="markers",
            marker_symbol="x",
            marker_size=10,
            marker_color="red",
            name="ShortPosition position",
        ),
        # Black dot located at (time, price) for quitting positions
        go.Scatter(
            x=trading_bot.df["CloseDate"][trading_bot.df["QuitPosition"] == 1],
            y=trading_bot.df["PositionPrice"][trading_bot.df["QuitPosition"] == 1],
            mode="markers",
            marker_symbol="circle-dot",
            opacity=0.5,
            marker_size=8,
            marker_color="black",
            name="Position quitted",
        ),
    ]
    childrens_graphs = []
    for i in trading_bot.indicators:
        # Adding the data of each indicator in the main graph
        for scatter in i.get_plot_scatters_for_main_graph(trading_bot.df):
            data.append(scatter)
        # Adding each indicator's plot in the dashboard
        if (indicator_graph := i.get_indicator_graph(trading_bot.df)) is not None:
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

    trade_reporting = go.Figure(
        data=[
            go.Table(
                header=dict(values=trading_reporting_columns),
                cells=dict(
                    values=trading_bot.trades_reporting[trading_reporting_columns]
                    .transpose()
                    .values.tolist(),
                    fill_color="lavender",
                    align="left",
                ),
            )
        ]
    )

    ################################################################################################
    #                    Here to make the vertical scaling automatic when zooming                  #
    ################################################################################################

    app = Dash()

    app.layout = html.Div(
        children=[
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
                + [
                    dcc.Graph(
                        id="trade_reporting",
                        figure=trade_reporting,
                        style=dict(
                            height=500,
                        ),
                    )
                ]
            ),
        ]
    )

    childrens_graphs_State = [State(plot.id, "figure") for plot in childrens_graphs]
    childrens_graphs_Output = [Output(plot.id, "figure") for plot in childrens_graphs]

    # Server side implementation (slow)
    @app.callback(
        [Output("graph_candlestick", "figure")]
        + childrens_graphs_Output
        + [Output("trade_reporting", "figure")],
        Input("graph_candlestick", "relayoutData"),
        [State("graph_candlestick", "figure")]
        + childrens_graphs_State
        + [State("trade_reporting", "figure")],
    )
    def update_result(relOut, Fig, *my_args):
        double_click_event = {"xaxis.autorange": True, "yaxis.autorange": True}

        # Last value will always be the reporting table.
        tradeReportingFig = my_args[-1]
        my_args = my_args[:-1]

        # When update is not specific
        if relOut is None:
            return Fig, *my_args, tradeReportingFig

        # When update is about changing the xaxis
        elif "xaxis.range[0]" in relOut.keys():

            ### Updating the x/y axis for the Candlestick graph
            Fig["layout"]["yaxis"]["range"] = get_extremum_between_range(
                df=trading_bot.df,
                x1=Timestamp(relOut["xaxis.range[0]"]),
                x2=Timestamp(relOut["xaxis.range[1]"]),
            )
            Fig["layout"]["yaxis"]["autorange"] = False

            ### Updating the x/y axis for the indicators graphs
            for plot in my_args:
                plot["layout"]["xaxis"]["autorange"] = False
                plot["layout"]["xaxis"]["range"] = [
                    relOut["xaxis.range[0]"],
                    relOut["xaxis.range[1]"],
                ]

            ### Updating the x/y boundaries for the Reporting table
            df = trading_bot.trades_reporting[
                (trading_bot.trades_reporting.EntryTime > relOut["xaxis.range[0]"])
                & (trading_bot.trades_reporting.ExitTime < relOut["xaxis.range[1]"])
            ][trading_reporting_columns]
            tradeReportingFig["data"] = [
                go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(
                        values=df.transpose().values.tolist(),
                        fill_color="lavender",
                        align="left",
                    ),
                )
            ]
            return Fig, *my_args, tradeReportingFig

        # When update is about reseting the xaxis
        elif relOut == double_click_event:
            for plot in my_args:
                plot["layout"]["xaxis"]["autorange"] = True
                plot["layout"]["yaxis"]["autorange"] = True
            df = trading_bot.trades_reporting[trading_reporting_columns]
            tradeReportingFig["data"] = [
                go.Table(
                    header=dict(values=list(df.columns)),
                    cells=dict(
                        values=df.transpose().values.tolist(),
                        fill_color="lavender",
                        align="left",
                    ),
                )
            ]
            return Fig, *my_args, tradeReportingFig

        else:
            return Fig, *my_args, tradeReportingFig

    app.run_server(port=1101)
    ################################################################################################
