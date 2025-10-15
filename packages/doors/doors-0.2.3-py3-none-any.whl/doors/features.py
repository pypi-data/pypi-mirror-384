# pylint: disable=invalid-name
import copy
from functools import partial

import numpy as np
import pandas as pd

from doors import np as wnp


def grouped_lagged_decay(df, groupby, col, fillna=0, decay=1):
    """Grouped lagged decay"""
    values = wnp.fillna(df[col].values, 0)
    f = partial(lagged_decay, decay=decay)
    result = wnp.group_apply(values, df[groupby].values, f)
    result = wnp.fillna(result, fillna)
    return result


def lagged_decay(ordered_values, decay=1):
    """lagged decay"""
    result = np.nan * ordered_values
    previous_value = np.nan
    historic_score = np.nan
    current_score = 0
    for i, value in enumerate(ordered_values):
        if i > 0:
            current_score = previous_value + historic_score * np.exp(-decay)
            result[i] = current_score
        previous_value = value
        historic_score = current_score
    return result


def days_to_first_event(df, groupby, time_col):
    """Calculate days to the first date for each group, in a Time series"""
    dates = df[time_col].astype("datetime64[ns]").values
    ids = df[groupby].values
    result = wnp.group_apply(dates, ids, _time_to_min_date)
    result = _convert_ns_to_days(result)
    return result


def _time_to_min_date(v):
    min_date = np.min(v)
    return v - min_date


def _convert_ns_to_days(values):
    return (((values / 1000000000) / 60) / 60) / 24


def grouped_days_since_result(
    df, groupby, col="win_flag", value=1, fillna=-1, coldate="scheduled_time"
):
    func = partial(days_since_result, value=1)
    result = wnp.group_apply(
        df[[col, coldate]].values, df[groupby].values, func, multiarg=True
    )
    result = wnp.fillna(result, fillna)
    return result


def days_since_result(
    v: np.ndarray | pd.Series,
    dates: np.ndarray | pd.core.indexes.datetimes.DatetimeIndex,
    value=1,
):
    """Number of days since the array was equal of higher than the given value"""
    if isinstance(dates, pd.core.indexes.datetimes.DatetimeIndex):
        dates = dates.astype("datetime64[ms]").values
    else:
        dates = dates.astype("datetime64[ms]")
    if isinstance(v, pd.Series):
        v = v.values

    date_of_last_win = copy.deepcopy(dates)
    win_ix = v >= value
    date_of_last_win[~win_ix] = np.datetime64("NaT")
    # just to shift: shove a nat to start, drop the last value
    date_of_last_win = np.r_[np.datetime64("NaT"), date_of_last_win[:-1]]
    date_of_last_win = wnp.ffill(date_of_last_win)
    diffs = (dates - date_of_last_win).astype("timedelta64[D]")
    nan_ix = wnp.isnull(diffs)
    diffs = diffs.astype(float)
    diffs[nan_ix] = np.nan
    return diffs


def grouped_ema(df: pd.DataFrame, col: str, n_period: float, groupby: str) -> pd.Series:
    """
    Calculate EMA for each group
    """
    func = partial(ema, n_period=n_period)
    result = df.groupby(groupby)[col].transform(func)
    return result


def ema(v: pd.Series, n_period=5):
    """Exponential moving average for a vector"""
    if n_period < 1:
        raise ValueError("n_period can't be less than 1")
    alpha = 2.0 / (1 + n_period)
    result = np.nan * np.zeros(len(v))
    vals = v.values
    result[0] = vals[0]
    for i in range(1, len(v)):
        result[i] = alpha * vals[i] + (1 - alpha) * result[i - 1]
    return result


def lagged_ema(v, n_period, shift=1, init=0):
    emas = ema(v, n_period)
    emas = wnp.lag(emas, init=init, shift=shift)
    return emas


def grouped_lagged_ema(
    df: pd.DataFrame, col: str, n_period: float, groupby: str, shift=1, init=0
) -> pd.Series:
    func = partial(lagged_ema, n_period=n_period, shift=shift, init=init)
    result = df.groupby(groupby)[col].transform(func)
    return result


def dema(v: pd.Series, n_period):
    """
    The Formula for the Double Exponential Moving Average Is:
    DEMA=2×EMA(n_period) − EMA of EMA(n_period)

    where:
    n_period = Look-back period
    """
    ema_v = pd.Series(ema(v, n_period))
    ema_of_ema = ema(ema_v, n_period)
    return (ema_v * 2) - ema_of_ema


def lagged_dema(v, n_periods):
    """needs test"""
    demas = dema(v, n_periods)
    demas = wnp.lag(demas, init=0)
    return demas


def categorical_to_numeric(df, column):
    """convert text column into numeric using the character codes"""

    def char_to_numeric(char):
        return str(ord(char))

    def text_to_numeric(text):
        text = str(text).strip()
        text = text[:10]
        text = text.lower()
        numeric_chars = map(char_to_numeric, text)
        result = "".join(numeric_chars)
        result = float(result)
        return result

    result = map(text_to_numeric, df[column])
    result = np.log(np.array(result))
    return result


def categorical_to_frequency(df, column):
    """convert categorical column using the frequency of elements"""
    ixs = wnp.get_group_ixs(df[column].values)
    res = np.zeros(len(df))
    for ix in ixs.values():
        res[ix] = len(ix)
    return res.astype(np.int64)


def rolling_func(v: pd.Series, window=4, func: str = "sum", fillna=-1) -> pd.Series:
    roll = v.rolling(window=window, min_periods=window)
    f = func.lower()
    if f == "sum":
        res = roll.sum()
    elif f == "mean":
        res = roll.mean()
    elif f == "median":
        res = roll.median()
    elif f == "max":
        res = roll.max()
    else:
        raise ValueError("fun must be 'sum', 'mean', 'median', 'max'")

    return res.fillna(fillna)


def lagged_rolling_func(
    v: pd.Series, window=4, func: str = "sum", fillna=-1, shift=1
) -> pd.Series:
    res = rolling_func(v, window=window, func=func, fillna=fillna)

    return res.shift(shift).fillna(fillna)


def grouped_lagged_rolling_func(
    df: pd.DataFrame,
    groupby: str,
    col: str,
    window: str,
    func: str,
    fillna: int,
    shift: int,
):
    """Grouped rolling func"""
    f = partial(
        lagged_rolling_func, window=window, func=func, fillna=fillna, shift=shift
    )
    return df.groupby(groupby)[col].transform(f)
