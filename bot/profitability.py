from bot.logging_formatter import bcolors


def get_impact(df, investment):
    try:
        bought_dates = df.index[df["BuyingSignal"] == 1]
        bought_prices = df.Open[bought_dates].reset_index()

        sold_dates = df.index[df["SellingSignal"] == 1]
        sold_prices = df.Open[sold_dates].reset_index()

        if len(bought_prices) == len(sold_prices) + 1:
            bought_prices.drop(bought_prices.tail(1).index, inplace=True)
        elif len(bought_prices) != len(sold_prices):
            raise Exception

        bought_prices_list = bought_prices.Open.tolist()
        bought_times_list = bought_prices.Time.tolist()
        sold_prices_list = sold_prices.Open.tolist()
        sold_times_list = sold_prices.Time.tolist()

        # This variable is needed to keep track of last "sold" value
        # First order is a long position. No short, so we set that var to first bought price for no impact on investment
        # As we start investment with a buy, when there is a selling signal we sold the position;
        # and open a new one that is shorting !! So we need to keep the value to compare it with next buying signal
        # (which will be the signal of solding the short position)
        _sold_price_memory = bought_prices_list[0]
        _sold_time_memory = bought_times_list[0]
        for bought_info, sold_info in zip(
            zip(bought_prices_list, bought_times_list),
            zip(sold_prices_list, sold_times_list),
        ):
            bought_price = bought_info[0]
            bought_time = bought_info[1]
            sold_price = sold_info[0]
            sold_time = sold_info[1]
            short_percentage = (_sold_price_memory - bought_price) / bought_price
            investment *= 1 + short_percentage
            print(
                f"{bcolors.BOLD}---------\n{bcolors.ENDC}"
                f"{bcolors.OKBLUE}Short: {_sold_price_memory}({_sold_time_memory}) -> {bought_price}({bought_time}) : {round(100*short_percentage, 3)}%",
                end=f"                           --- {round(investment, 3)}\n{bcolors.ENDC}",
            )
            long_percentage = (sold_price - bought_price) / bought_price
            investment *= 1 + long_percentage
            print(
                f"{bcolors.OKGREEN}Long: {bought_price}({bought_time}) -> {sold_price}({sold_time}) : {round(100 * long_percentage, 3)}%",
                end=f"                           --- {round(investment, 3)}\n{bcolors.ENDC}",
            )
            _sold_price_memory = sold_price
            _sold_time_memory = sold_time

        return investment
    except Exception:
        return 0
