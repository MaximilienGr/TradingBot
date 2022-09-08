from bot.logging_formatter import bcolors


def get_impact(df, investment):
    try:
        initial_investment = investment
        long_position_dates = df.index[df["LongPosition"] == 1]
        # TODO: Il faut prendre Open plutot ? Confusion sur le prix a prendre
        long_position_prices = df.Close[long_position_dates].reset_index()

        short_position_dates = df.index[df["ShortPosition"] == 1]
        short_position_prices = df.Close[short_position_dates].reset_index()

        if abs(len(long_position_prices) - len(short_position_prices)) == 1:
            long_position_prices.drop(long_position_prices.tail(1).index, inplace=True)
        elif len(long_position_prices) != len(short_position_prices):
            raise Exception

        long_position_prices_list = long_position_prices.Close.tolist()
        # TODO: Open time?
        long_position_times_list = long_position_prices.OpenTime.tolist()
        short_position_prices_list = short_position_prices.Close.tolist()
        short_position_times_list = short_position_prices.OpenTime.tolist()

        _short_position_price_memory = long_position_prices_list[0]
        _short_position_time_memory = long_position_times_list[0]
        for long_position_info, short_position_info in zip(
            zip(long_position_prices_list, long_position_times_list),
            zip(short_position_prices_list, short_position_times_list),
        ):
            long_position_price = long_position_info[0]
            long_position_time = long_position_info[1]
            short_position_price = short_position_info[0]
            short_position_time = short_position_info[1]
            short_percentage = (
                _short_position_price_memory - long_position_price
            ) / long_position_price
            investment *= 1 + short_percentage
            print(
                f"{bcolors.BOLD}---------\n{bcolors.ENDC}"
                f"{bcolors.OKBLUE}Short: {_short_position_price_memory}({_short_position_time_memory}) -> {long_position_price}({long_position_time}) : {round(100*short_percentage, 3)}%",
                end=f"                           --- {round(investment, 3)}\n{bcolors.ENDC}",
            )
            long_percentage = (
                short_position_price - long_position_price
            ) / long_position_price
            investment *= 1 + long_percentage
            print(
                f"{bcolors.OKGREEN}Long: {long_position_price}({long_position_time}) -> {short_position_price}({short_position_time}) : {round(100 * long_percentage, 3)}%",
                end=f"                           --- {round(investment, 3)}\n{bcolors.ENDC}",
            )
            _short_position_price_memory = short_position_price
            _short_position_time_memory = short_position_time

        rentability_percentage = (
            100 * (investment - initial_investment) / initial_investment
        )
        print(
            f"For an initial investment of {initial_investment} $: {investment}."
            f" --> {round(rentability_percentage, 2)} %"
        )

        return investment
    except Exception:
        return 0
