import mplcursors
from matplotlib import pyplot as plt


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
    plt.bar(up.CloseDate, up.Close - up.Open, width, bottom=up.Open, color=col1)
    plt.bar(up.CloseDate, up.High - up.Close, width2, bottom=up.Close, color=col1)
    plt.bar(up.CloseDate, up.Low - up.Open, width2, bottom=up.Open, color=col1)

    # plot down prices
    plt.bar(down.CloseDate, down.Close - down.Open, width, bottom=down.Open, color=col2)
    plt.bar(down.CloseDate, down.High - down.Open, width2, bottom=down.Open, color=col2)
    plt.bar(
        down.CloseDate, down.Low - down.Close, width2, bottom=down.Close, color=col2
    )

    # rotate x-axis tick labels
    plt.xticks(rotation=45, ha="right")

    # define the moments of buying
    bought_dates = df.CloseDate[df["LongSignal"] == 1]
    bought_prices = df.PositionPrice[bought_dates]

    # plot the buying points
    plt.scatter(
        x=bought_prices.OpenTime.tolist(),
        y=bought_prices.Open.tolist(),
        marker=4,
        color="c",
        s=250,
    )

    # define the moments of selling
    sell_dates = df.index[df["ShortSignal"] == 1]
    sell_prices = df.PositionPrice[sell_dates].reset_index()

    # plot the selling moments
    plt.scatter(
        x=sell_prices.OpenTime.tolist(),
        y=sell_prices.PositionPrice.tolist(),
        marker=4,
        color="m",
        s=250,
    )

    mplcursors.cursor(hover=True)

    # display candlestick chart
    plt.show()
