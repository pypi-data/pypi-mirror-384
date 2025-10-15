import numpy as np


def gaussian_function(x, location, height, width):
    """For all elements in the input array, calculate values of
    the Gaussian function given as:

    f(x) = height * e^(-(x-location)^2 / (2*width^2))

    where e is the constant, the base of the natural logarithm (~ 2.718).

    Args:
        x (array_like): input values
        location (scalar): function parameter
        height (scalar): function parameter
        width (scalar): function parameter

    Returns:
        array_like: values of the gaussian function
    """
    fx = height * np.exp(-((x - location) ** 2) / (2 * width**2))
    return fx


def peaks_to_gaussian(x, peaks=None):
    """
    Return signal composed of sum of the gaussians of all the peaks.

    For each peak, the gaussian is fitted using the
    gaussian_function(x, location, height, width)
    function.

    Merging is achieved by summing the individual gaussians.

    Args:
        x (array): the independent variable axis.
        peaks (list): list of dictionaries, containing location, width and
            height of each peak.

    Returns:
        array: An numpy.array containing the y values for the gausian function.

    """

    # this is to avoid having peaks be a mutable default argument
    if peaks is None:
        peaks = [{"height": None, "location": None, "width": None}]

    gaussians = [gaussian_function(x, **peak) for peak in peaks]
    gaussians_merged = np.sum(gaussians, axis=0)

    return gaussians_merged
