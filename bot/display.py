import mplcursors
from matplotlib import pyplot as plt
from dash import Output, Input, State, dcc, html, Dash
import plotly.graph_objects as go


def show_candlestick(df, width=4, width2=0.5):
    # create figure
    plt.figure(figsize=(20, 10))

    # define up and down prices
    up = df[df.Close >= df.Open]
    down = df[df.Close < df.Open]

    # define colors to use
    col1 = "green"
    col2 = "red"

    # plot up prices
    plt.bar(up.index, up.Close - up.Open, width, bottom=up.Open, color=col1)
    plt.bar(up.index, up.High - up.Close, width2, bottom=up.Close, color=col1)
    plt.bar(up.index, up.Low - up.Open, width2, bottom=up.Open, color=col1)

    # plot down prices
    plt.bar(down.index, down.Close - down.Open, width, bottom=down.Open, color=col2)
    plt.bar(down.index, down.High - down.Open, width2, bottom=down.Open, color=col2)
    plt.bar(down.index, down.Low - down.Close, width2, bottom=down.Close, color=col2)

    # rotate x-axis tick labels
    plt.xticks(rotation=45, ha="right")

    # define the moments of buying
    bought_dates = df.index[df["Bought"] == 1]
    bought_prices = df.Open[bought_dates].reset_index()

    # plot the buying points
    plt.scatter(
        x=bought_prices.Time.tolist(),
        y=bought_prices.Open.tolist(),
        marker=4,
        color="c",
        s=250,
    )

    # define the moments of selling
    sell_dates = df.index[df["Sell"] == 1]
    sell_prices = df.Open[sell_dates].reset_index()

    # plot the selling moments
    plt.scatter(
        x=sell_prices.Time.tolist(),
        y=sell_prices.Open.tolist(),
        marker=4,
        color="m",
        s=250,
    )

    mplcursors.cursor(hover=True)

    # display candlestick chart
    plt.show()


def show_candlestick_with_plotly(df):

    graph_candlestick = go.Figure(
        data=[
            go.Candlestick(
                x=df["Timestamp"],
                open=df["Open"],
                high=df["High"],
                low=df["Low"],
                close=df["Close"],
            ),
            go.Scatter(
                x=df["Timestamp"][df["Bought"] == 1],
                y=df["Open"][df["Bought"] == 1],
                mode="markers",
                marker_symbol="arrow-up",
                marker_size=10,
                marker_color="green",
                name="Buying position",
            ),
            go.Scatter(
                x=df["Timestamp"][df["Sell"] == 1],
                y=df["Open"][df["Sell"] == 1],
                mode="markers",
                marker_symbol="arrow-down",
                marker_size=10,
                marker_color="red",
                name="Selling position",
            ),
        ]
    )

    ################################################################################################
    # Here to make the vertical scaling automatic when zooming

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
                yaxis=dict(autorange=True),
                template="plotly",
            )

            Fig["layout"] = newLayout
            return Fig

        else:
            ymin = df.loc[
                df["Timestamp"].between(
                    relOut["xaxis.range[0]"], relOut["xaxis.range[1]"]
                ),
                "Low",
            ].min()
            ymax = df.loc[
                df["Timestamp"].between(
                    relOut["xaxis.range[0]"], relOut["xaxis.range[1]"]
                ),
                "High",
            ].max()

            newLayout = go.Layout(
                height=600,
                width=1300,
                showlegend=True,
                xaxis=dict(
                    rangeslider_visible=True,
                    range=[relOut["xaxis.range[0]"], relOut["xaxis.range[1]"]],
                ),
                yaxis=dict(range=[ymin, ymax]),
                template="plotly",
            )

            Fig["layout"] = newLayout
            return Fig

    app.run_server(debug=True, port=1101)
    ################################################################################################
    # graph_candlestick.show()
