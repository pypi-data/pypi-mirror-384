""" functions to deal with clargs """
import sys

import numpy as np


def get_args():
    """get args from command line"""
    args = sys.argv
    dot_py_ix = np.where([".py" in arg for arg in args])[0][0]
    args = args[(dot_py_ix + 1) :]
    return args
