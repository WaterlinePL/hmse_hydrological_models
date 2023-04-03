import datetime


def float_to_julian(day_num: float) -> float:
    return round(day_num % 365, 2)


def date_to_julian(date: str):
    # Format: M/D/YYYY
    fmt = "%m/%d/%Y"
    dt = datetime.datetime.strptime(date, fmt)
    return dt.timetuple().tm_yday
