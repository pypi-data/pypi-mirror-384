"""Set of tools to help with vectorial calculations and cleaning"""

from collections import OrderedDict, defaultdict

import numpy as np
import pandas as pd

# from numba import jit

# pylint: disable=missing-docstring
# pylint: disable=invalid-name


def IQR(v):
    """Caclualtes interquantile range"""
    series = pd.Series(v)
    q75 = series.quantile(0.75)
    q25 = series.quantile(0.25)
    return q75 - q25


def moving_average(array, window, center=False, min_periods=1):
    """may be not the fastest option for long arrays"""
    return (
        pd.DataFrame(array)
        .rolling(window, center=center, min_periods=min_periods)
        .mean()
        .to_numpy()
        .squeeze()
    )


def moving_median(array, window, center=False):
    """may be not the fastest option for long arrays"""
    return (
        pd.DataFrame(array)
        .rolling(window, center=center, min_periods=1)
        .median()
        .values.squeeze()
    )


# @jit(nopython=True)
def fillna(array, na_value):
    array = array.copy()
    ix = np.isnan(array) | np.isinf(array)
    if np.isscalar(na_value):
        array[ix] = na_value
    else:
        array[ix] = na_value[ix]
    return array


def get_str_columns(df):
    str_columns = [
        col for col in df.columns if not np.issubdtype(df[col].dtype, np.number)
    ]
    return str_columns


def flatten(lst):
    return [item for sublist in lst for item in sublist]


def ensure_is_list(obj):
    return obj if isinstance(obj, list) else [obj]


def ix_to_bool(ix, length):
    boolean_mask = np.repeat(False, length)
    boolean_mask[ix] = True
    return boolean_mask


def concatenate(data, fill_na=None):
    all_keys = [d.keys() for d in data]
    flat_keys = [k for keys in all_keys for k in keys]
    keys = set(flat_keys)
    _data = {k: [] for k in keys}
    for row in data:
        for k in keys:
            _data[k].append(row.get(k, fill_na))
    return _data


def is_nptimedelta(v):
    try:
        answer = "timedelta" in v.dtype.name
    except:  # noqa E722
        answer = False
    return answer


def is_datetime(v):
    return "datetime" in str(v.dtype)


def simple_group_apply(values, group_ids, func):
    output = np.repeat(np.nan, len(values))
    ixs = get_group_ixs(group_ids)
    for ix in ixs.values():
        output[ix] = func(values[ix])
    return output


def group_apply(values, group_ids, func, multiarg=False, strout=False):
    if group_ids.ndim == 2:
        group_ids = add_as_strings(
            *[group_ids[:, i] for i in range(group_ids.shape[1])], sep="_"
        )

    ix = np.argsort(group_ids, kind="mergesort")
    sids = group_ids[ix]
    cuts = sids[1:] != sids[:-1]
    reverse = invert_argsort(ix)
    values = values[ix]

    if strout:
        nvalues = np.prod(values.shape)
        res = np.array([None] * nvalues).reshape(values.shape)
    elif multiarg:
        res = np.nan * np.zeros(len(values))
    else:
        res = np.nan * np.zeros(values.shape)

    prevcut = 0
    for cut in np.where(cuts)[0] + 1:
        if multiarg:
            res[prevcut:cut] = func(*values[prevcut:cut].T)
        else:
            res[prevcut:cut] = func(values[prevcut:cut])
        prevcut = cut
    if multiarg:
        res[prevcut:] = func(*values[prevcut:].T)
    else:
        res[prevcut:] = func(values[prevcut:])
    revd = res[reverse]
    return revd


def invert_argsort(argsort_ix):
    reverse = np.repeat(0, len(argsort_ix))
    reverse[argsort_ix] = np.arange(len(argsort_ix))
    return reverse


def add_as_strings(*args, **kwargs):
    result = args[0].astype(str)
    sep = kwargs.get("sep")
    if sep:
        seperator = np.repeat(sep, len(result))
    else:
        seperator = None

    for arr in args[1:]:
        if seperator is not None:
            result = _add_strings(result, seperator)
        result = _add_strings(result, arr.astype(str))
    return result


def _add_strings(v, w):
    return np.core.defchararray.add(v, w)


def get_group_ixs(*group_ids, **kwargs):
    """Returns a dictionary {groupby_id: group_ix}.

    group_ids:
        List of IDs to groupbyy
    kwargs:
        bools = True or False, if True returns a boolean array
    """
    group_ids = _ensure_group_ids_hashable(group_ids)
    grouped_ixs = _get_group_ixs(group_ids)
    grouped_ixs = _convert_int_indices_to_bool_indices_if_necessary(grouped_ixs, kwargs)
    return grouped_ixs


def _ensure_group_ids_hashable(group_ids):
    if len(group_ids) == 1:
        combined_group_ids = group_ids[0]
    else:
        combined_group_ids = zip(*group_ids)
    is_list_of_list = lambda ids: isinstance(ids[0], list)  # noqa E731
    is_matrix = lambda ids: isinstance(ids, np.ndarray) and ids.ndim == 2  # noqa E731
    if is_list_of_list(combined_group_ids) or is_matrix(combined_group_ids):
        hashable_group_ids = [tuple(group_id) for group_id in combined_group_ids]
    else:
        hashable_group_ids = combined_group_ids
    return hashable_group_ids


def _convert_int_indices_to_bool_indices_if_necessary(ixs, kwargs):
    bools = kwargs.get("bools", False)
    if bools:
        length = np.sum([len(v) for v in ixs.values()])
        ix_to_bool = lambda v, length: np.ix_to_bool(v, length)  # noqa E731
        ixs = {k: ix_to_bool(v, length) for k, v in ixs.items()}
    return ixs


def _get_group_ixs(ids):
    id_hash = defaultdict(list)
    for j, key in enumerate(ids):
        id_hash[key].append(j)
    id_hash = {k: np.array(v) for k, v in id_hash.items()}
    return id_hash


def get_ordered_group_ixs(group_ids):
    od_ixs = OrderedDict()
    for i, val in enumerate(group_ids):
        if val in od_ixs:
            od_ixs[val].append(i)
        else:
            od_ixs[val] = [i]
    return od_ixs


def get_unique_values_in_order(values):
    return list(OrderedDict.fromkeys(values))


def change_flag(arr, init=0):
    """[1,1,2,3,1] --> [init, 0, 1, 1, 1]"""
    values = np.repeat(None, len(arr))
    values[0] = 0
    values[1:] = (arr[1:] != arr[:-1]).astype(int)
    return values


def get_new_value_flags(values):
    """Goes through the values and flags unique values it has not seen before.
    Example:
        values = [A, B, C, A, A, D] --> [True, True, True, False, False, True]
    """
    _, indices = np.unique(values, return_index=True)
    flags = np.zeros(len(values))
    flags[indices] = 1
    return flags.astype(bool)


def is_npdatetime(v):
    try:
        answer = "datetime" in v.dtype.name
    except:  # noqa E722
        answer = False
    return answer


def nan_allclose(x, y):
    nan_ix_x = np.isnan(x)
    nan_ix_y = np.isnan(y)
    is_close = np.isclose(x, y)
    nan_close = is_close | (nan_ix_x & nan_ix_y)
    return np.all(nan_close)


def ffill(values):
    """vector only"""
    assert len(values.shape) == 1 or values.shape[1] == 1, "ffill only works for vector"
    values = np.atleast_2d(values)
    mask = is_null(values)
    idx = np.where(~mask, np.arange(mask.shape[1]), 0)
    idx = np.maximum.accumulate(idx, axis=1, out=idx)
    out = values[np.arange(idx.shape[0])[:, None], idx]
    out = out.squeeze()
    return out


def is_null(*args, **kwargs):
    return pd.isnull(*args, **kwargs)


isnull = is_null


# @jit(nopython=True)
def lag(v, init, shift=1):
    w = np.nan * v
    w[0:shift] = init
    w[shift:] = v[:-shift]
    return w


def lagged_cumsum(v, init, shift=1):
    return lag(np.cumsum(v, axis=0), init, shift=shift)


def rank(array):
    """
    Returns rank of element in an array, with greatest value having the greatest
    rank. Repeated values get different ranks.

    Examples:
        [-10, 3, 0, 0] ==> [0, 3, 1, 2]
        [10, 7, 6] ==> [2, 1, 0]
    """
    temp = array.argsort()
    ranks = np.empty(len(array), int)
    ranks[temp] = np.arange(len(array))
    return ranks


def rolling_mean(v, window):
    out = np.nan * v
    cumsums = np.cumsum(v)
    length = len(v)
    if length <= window:
        out = 1.0 * cumsums / (np.arange(length) + 1)
    else:
        out[:window] = 1.0 * cumsums[:window] / (np.arange(window) + 1)
        out[window:] = (cumsums[window:] - cumsums[: length - window]) / window
    return out


def get_rolling_std(v, window):
    rolling_means = rolling_mean(v, window)
    deviation = (v - rolling_means) ** 2
    cum_deviation = np.cumsum(deviation)
    diff = cum_deviation[window:] - cum_deviation[:-window]
    mean_diff = diff / window
    for i in range(min(window, len(v))):
        mean_diff = np.insert(mean_diff, i, cum_deviation[i] / (i + 1))
    return np.sqrt(mean_diff)


def get_rolling_sharpe(v, window):
    rolling_means = rolling_mean(v, window)
    rolling_std = get_rolling_std(v, window)
    return rolling_means / rolling_std


# Losses
def bin_ent(flags, predictions):
    assert flags.shape == predictions.shape
    losses = -(flags * np.log(predictions) + (1.0 - flags) * np.log(1.0 - predictions))
    return losses


def mean_bin_ent(flags, predictions):
    return bin_ent(flags, predictions).mean()


def sq_loss(targets, predictions):
    assert targets.shape == predictions.shape
    losses = (predictions - targets) ** 2
    return losses


def mean_sq_loss(targets, predictions):
    return sq_loss(targets, predictions).mean()


def abs_loss(targets, predictions):
    assert targets.shape == predictions.shape
    losses = np.abs(predictions - targets)
    return losses


def mean_abs_loss(targets, predictions):
    return abs_loss(targets, predictions).mean()


def x_ent(flags, predictions):
    _check_x_ent_inputs(predictions, flags)
    losses = -flags * np.log(predictions)
    return losses


def mean_x_ent(flags, predictions):
    return x_ent(flags, predictions).mean()


def _check_x_ent_inputs(predictions, flags):
    sum_preds = np.sum(predictions, axis=1)
    assert np.all(
        np.isclose(sum_preds, 1.0)
    ), "Predictions do not sum to one in probability space"
    assert sorted(np.unique(flags)) == [0.0, 1.0]
