# pylint: disable=invalid-name
# pylint: disable=missing-docstring

import numpy as np


def group_mean_log_mae(y_true, y_pred, groups, floor=1e-9):
    maes = (y_true - y_pred).abs().groupby(groups).mean()
    return np.log(maes.map(lambda x: max(x, floor))).mean()
