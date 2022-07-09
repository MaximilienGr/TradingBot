from datetime import datetime


def date_to_mili_timestamp(date):
    return int(datetime.strptime(date, "%d.%m.%Y %H:%M:%S").timestamp() * 1000)
