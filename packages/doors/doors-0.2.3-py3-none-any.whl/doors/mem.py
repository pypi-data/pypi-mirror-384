import numpy as np


def reduce_mem_usage(data, verbose=True, skip_cols=()):  # noqa: C901
    """reduce memory consumption for Pandas data frames"""

    def reduce_int():
        if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
            return data[col].astype(np.int8)
        if c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
            return data[col].astype(np.int16)
        if c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
            return data[col].astype(np.int32)
        if c_min > np.iinfo(np.int64).min and c_max < np.iinfo(np.int64).max:
            return data[col].astype(np.int64)
        return data[col]

    def reduce_float():
        if c_min > np.finfo(np.float16).min and c_max < np.finfo(np.float16).max:
            return data[col].astype(np.float16)
        if c_min > np.finfo(np.float32).min and c_max < np.finfo(np.float32).max:
            return data[col].astype(np.float32)

        return data[col].astype(np.float64)

    numerics = ["int16", "int32", "int64", "float16", "float32", "float64"]
    start_mem = data.memory_usage().sum() / 1024**2
    columns = sorted(set(list(data.columns)) - set(skip_cols))
    for col in columns:
        col_type = data[col].dtypes
        if col_type in numerics:
            c_min = data[col].min()
            c_max = data[col].max()
            if str(col_type)[:3] == "int":
                data[col] = reduce_int()
            else:
                data[col] = reduce_float()
    end_mem = data.memory_usage().sum() / 1024**2
    if verbose:
        print(
            "Mem. usage decreased to {:5.2f} Mb ({:.1f}%\
        reduction)".format(
                end_mem, 100 * (start_mem - end_mem) / start_mem
            )
        )
    return data
