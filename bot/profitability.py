def get_impact(df):
    bought_dates = df.index[df["Bought"] == 1]
    bought_prices = df.Open[bought_dates].reset_index()

    sold_dates = df.index[df["Sold"] == 1]
    sold_prices = df.Open[sold_dates].reset_index()

    if len(bought_prices) == len(sold_prices) + 1:
        bought_prices.drop(bought_prices.tail(1).index, inplace=True)
    elif len(bought_prices) != len(sold_prices):
        raise Exception

    bought_prices_list = bought_prices.Open.tolist()
    sold_prices_list = sold_prices.Open.tolist()
    impact = 0
    for bought, sold in zip(bought_prices_list, sold_prices_list):
        impact += (sold - bought) / bought

    impact /= len(bought_prices)
    return impact * 100
