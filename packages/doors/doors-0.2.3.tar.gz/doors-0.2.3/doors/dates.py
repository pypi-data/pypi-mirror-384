import datetime
import re

import numpy as np
import pandas as pd


def get_day_of_year(dates):
    return _get_timestamp_attribute(dates, "dayofyear")


def get_day_of_week(dates):
    return pd.Series(dates).apply(lambda x: x.weekday()).values


def get_hour(dates):
    return _get_timestamp_attribute(dates, "hour")


def get_month(dates):
    return _get_timestamp_attribute(dates, "month")


def get_week(dates):
    return _get_timestamp_attribute(dates, "week")


def _get_timestamp_attribute(dates, attr):
    timestamps = pd.Series(dates)
    result = timestamps.apply(lambda x: getattr(x, attr)).values
    return result


def extract_timestamp(string):
    regex_expression = "[1-2][0-9]{1,7}_[0-9]{1,6}"
    result = re.search(regex_expression, string)
    if result:
        timestamp = result.group(0)
    else:
        raise ValueError("no timestamp found.")
    return timestamp


def replace_timestamp(string):
    timestamp = extract_timestamp(string)
    new_string = string.replace(timestamp, get_timestamp())
    return new_string


def get_diff_in_days(dates, add_init=False):
    """Gives the difference in days for datetime64 objects"""
    diff_date = np.diff(dates)
    delta_minutes = diff_date.astype("timedelta64[m]") / np.timedelta64(1, "m")
    delta_days = 1.0 * delta_minutes / (60 * 24)
    if add_init:
        delta_days = np.concatenate([[np.nan], delta_days])
    return delta_days


def cum_diff_years(dates, init=0):
    """Calculates cumulative difference in years betweeon dates[i] and date[]"""
    experience_days = np.empty(len(dates))
    experience_days[1:] = np.cumsum(get_diff_in_days(dates))
    experience_days[0] = init
    experience_years = experience_days / 365
    return experience_years


def get_months(dates):
    return dates.astype("datetime64[M]").astype(int) % 12 + 1


def get_datetime_now():
    return datetime.datetime.now(datetime.timezone.utc)


def get_datetime_end_of_day():
    now = get_datetime_now()
    return datetime.datetime(now.year, now.month, now.day, 23, 59, 59)


def get_datetime_start_of_month():
    this_morning = get_datetime_this_morning()
    start_of_month = this_morning.replace(day=1)
    return start_of_month


def get_datetime_this_morning():
    now = get_datetime_now()
    this_morning = datetime.datetime(year=now.year, month=now.month, day=now.day)
    return this_morning


def get_datetime_tomorrow_morning():
    this_morning = get_datetime_this_morning()
    tomorrow = this_morning + datetime.timedelta(days=1)
    return tomorrow


def get_datetime_yesterday_morning():
    this_morning = get_datetime_this_morning()
    tomorrow = this_morning - datetime.timedelta(days=1)
    return tomorrow


def get_datetime_last_week():
    this_morning = get_datetime_this_morning()
    tomorrow = this_morning - datetime.timedelta(days=7)
    return tomorrow


def round_datetime64(v, to="s"):
    # can replace this with v.astype('datetime64[{}]'.format(to))
    if to == "s":
        decimals = -9
    elif to == "m":
        decimals = -10
    else:
        assert isinstance(to, int), "Unexpected to."
        decimals = to
    return np.round(v.astype(np.int64), decimals).astype("datetime64[ns]")


def get_timestamp(time_format="%Y%m%d_%H%M%S"):
    """Returns a timestamp by checking the date and time at the moment."""
    return str(datetime.datetime.utcnow().strftime(time_format))


def is_datetime(v):
    return "datetime" in str(v.dtype)


def get_all_dates_in_range(start_date, end_date=None):
    if end_date is None:
        end_date = datetime.datetime.now().date()
    assert isinstance(start_date, datetime.date)
    assert isinstance(end_date, datetime.date)
    n_days = (end_date - start_date).days + 1  # include the max date
    all_days = [start_date + datetime.timedelta(n) for n in range(n_days)]
    return all_days


def get_season(day_number):
    day_spring_start = 80
    day_summer_start = 172
    day_autumn_start = 264
    day_winter_start = 356
    if (day_number < day_spring_start) | (day_number >= day_winter_start):
        return "winter"
    if day_number < day_summer_start:
        return "spring"
    if day_number < day_autumn_start:
        return "summer"
    if day_number < day_winter_start:
        return "autumn"
