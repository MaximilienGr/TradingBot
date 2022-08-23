def get_impact(df, investment):
    try:
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
        print("--- investment")
        for bought, sold in zip(bought_prices_list, sold_prices_list):
            percentage = (sold - bought) / bought
            investment *= 1 + percentage
            print(
                f"{bought} -> {sold} : {round(100*percentage, 3)}%       --- {investment}"
            )

        return investment
    except Exception:
        return 0
