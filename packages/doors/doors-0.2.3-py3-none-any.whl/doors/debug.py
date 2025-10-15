import time
from functools import partial

from doors.setup_logger import get_logger

LOGGER = get_logger(__name__)


def time_func(func):
    """A decorator that will print the time a function took to run."""

    def time_func_wrapped(*args, **kwargs):
        func_name = _get_func_name(func)

        start_time = time.time()
        out = func(*args, **kwargs)
        stop_time = time.time()

        exec_time = stop_time - start_time
        LOGGER.info(f"Time Func: '{func_name}' call took {exec_time: .4f}s.")

        # This makes the execution time available within this namespace
        globals()["_last_func_execution_time"] = exec_time
        return out

    return time_func_wrapped


def _get_func_name(func):
    """Defines a general convention for giving labels to functions."""
    if hasattr(func, "__name__"):
        func_name = func.__name__
    elif isinstance(func, partial):
        func_name = _make_partial_function_name(func)
    else:
        func_name = "Unnamed function (Theano?)"
    return func_name


def _make_partial_function_name(funcn):
    """Defines convention to labelling a partialised function."""
    assert isinstance(funcn, partial), "This function requires a partial fn."
    out = funcn.func.__name__
    for key, value in funcn.keywords.iteritems():
        if callable(value):
            value = value.__name__
        out += "_[" + key + "=" + str(value) + "]"
    return out
