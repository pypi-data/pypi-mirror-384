# pylint: disable=missing-docstring
# pylint: disable=invalid-name
import functools
import re

# import unicodedata
from string import punctuation as PUNCTUATIONS

import numpy as np

from doors.dates import get_timestamp

SPECIAL_PUNCTUATIONS = PUNCTUATIONS.replace("_", "")


def not_is_feat(col):
    return not is_feat(col)


def is_feat(col):
    return "feat:" in col


def clean_string(string):
    return string.lower().rstrip().replace(" ", "_").replace("'", "")


def to_lowercase(strings):
    strings = [string.lower() for string in strings]
    return strings


def get_pronounceable_name():
    consonants = ["b", "d", "f", "g", "h", "j", "k", "l", "m", "n", "p", "r", "s", "t"]
    vowels = ["a", "e", "i", "o", "u"]
    final_consonants = ["b", "f", "k", "l", "m", "n", "r", "s", "t"]
    return (
        np.random.choice(consonants)
        + np.random.choice(vowels)
        + np.random.choice(consonants)
        + np.random.choice(vowels)
        + np.random.choice(final_consonants)
    )


def get_unique_id():
    """Pronounceable hash to be pronounced more or less ecclesiastically.
    More details: https://www.ewtn.com/expert/answers/ecclesiastical_latin.htm
    """
    return get_pronounceable_name() + "_" + get_timestamp("%y%m%d_%H%M%S")


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


def camelcase_to_underscore(string):
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", string)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def remove_punctuation(string):
    for punctuation in SPECIAL_PUNCTUATIONS:
        string = string.replace(punctuation, "")
    return string


# def utf_to_ascii(string):
#     uni_string = unicode(string, "utf")
#     ascii_string = unicodedata.normalize("NFKD", uni_string).encode("ascii", "ignore")
#     return ascii_string


def is_ascii(string):
    try:
        string.decode("ascii")
        return True
    except UnicodeDecodeError:
        return False


def as_string(obj):
    if hasattr(obj, "__name__"):
        representation = obj.__name__
    elif isinstance(obj, functools.partial):
        representation = _get_partial_representation(obj)
    elif hasattr(obj, "__dict__"):
        representation = get_class_representation(obj)
    elif hasattr(obj, "__name__"):
        representation = obj.__name__
    else:
        representation = str(obj)
    return representation


def _get_partial_representation(obj):
    func_rep = as_string(obj.func)
    input_rep = "func=" + func_rep
    if _args_provided(obj):
        arg_rep = _get_arg_representation(obj.args)
        input_rep += ", " + arg_rep
    if _kwargs_provided(obj):
        kwarg_rep = get_dict_string_representation(obj.keywords)
        input_rep += ", " + kwarg_rep
    partial_rep = "partial({})".format(input_rep)
    return partial_rep


def _kwargs_provided(obj):
    return len(obj.keywords) > 0


def _args_provided(obj):
    return len(obj.args) > 0


def _get_arg_representation(args):
    return ", ".join([str(arg) for arg in args])


def get_class_representation(obj):
    joint_str_rep = get_dict_string_representation(obj.__dict__)
    cls_name = obj.__class__.__name__
    return "{}({})".format(cls_name, joint_str_rep)


def get_dict_string_representation(dct):
    str_rep = []
    for key, value in dct.items():
        if key[0] != "_":
            value_representation = as_string(value)
            str_rep.append("{}={}".format(key, value_representation))
    joint_str_rep = ", ".join(str_rep)
    return joint_str_rep


def convert_camelcase(camelcase):
    """
    Credit to:
    http://stackoverflow.com/questions/1175208/elegant-python-function-to-convert-
    camelcase-to-snake-case
    """
    s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", camelcase)
    return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


def clean_white_space(array):
    array = np.array([_clean_white_space(i) for i in array])
    return array


def _clean_white_space(v):
    if isinstance(v, str):
        v = v.strip(" ")
    return v
