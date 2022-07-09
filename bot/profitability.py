def get_impact(df):
    bought_dates = df.index[df["Bought"] == 1]
    bought_prices = df.Open[bought_dates].reset_index()

    sell_dates = df.index[df["Sell"] == 1]
    sell_prices = df.Open[sell_dates].reset_index()

    if len(bought_prices) == len(sell_prices) + 1:
        bought_prices.drop(bought_prices.tail(1).index, inplace=True)
    elif len(bought_prices) != len(sell_prices):
        raise Exception

    bought_prices_list = bought_prices.Open.tolist()
    sell_prices_list = sell_prices.Open.tolist()
    impact = 0
    for bought, sell in zip(bought_prices_list, sell_prices_list):
        impact += (sell - bought) / bought

    impact /= len(bought_prices)
    return impact * 100
