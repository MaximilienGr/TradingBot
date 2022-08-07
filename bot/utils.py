import random
from datetime import datetime


def date_to_mili_timestamp(date):
    return int(datetime.strptime(date, "%d.%m.%Y %H:%M:%S").timestamp() * 1000)


def get_random_color() -> str:
    return "#" + "".join([random.choice("ABCDEF0123456789") for i in range(6)])
