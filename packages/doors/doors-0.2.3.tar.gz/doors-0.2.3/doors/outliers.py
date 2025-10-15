""" functions to deal with outliers """
import numpy as np

# pylint: disable=invalid-name


def is_tukey_fences_inlier(array, tukey_fences_k=1.5):
    """Identify inliers by using Tukey Fences.

    Tukey Fences are a pair of commonly used thresholds for detecting outliers
    in 1d data:
        The lower threshold is defined by Q1 - 1.5*IQR.
        The upper threshold is defined by Q3 + 1.5*IQR.
        Data in between are inliers.

    Args:
        array (array-like): a 1d array of numbers.

    Returns:
        numpy array:
            A 1d boolean array whose length is the same as the input array.
            Inliers are marked with True, outliers are marked with False.

    Raises:
        ValueError:
            'The input array should only contain finite numbers.'
    """
    if not all(np.isfinite(array)):
        raise ValueError("The input array should only contain finite numbers.")

    if isinstance(array, np.ndarray):
        x = array
    else:
        x = np.array(array)

    q1 = np.percentile(x, 25)
    q3 = np.percentile(x, 75)
    iqr = q3 - q1
    return np.logical_and(
        x <= q3 + tukey_fences_k * iqr, x >= q1 - tukey_fences_k * iqr
    )
