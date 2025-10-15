""" dict functions """


def flatten_dict(nested: dict) -> dict:
    """Take a nested dictionary and flatten it. For example:
    {'a': {'b': 'c'}} will be flattened to {'a_b': c}
    Args:
        nested: a dictionary to be flattened
    Returns:
        Dict. flattened version of the original dictionary

    """
    ans = {}
    for key, val in nested.items():
        # if val is a dict, unflatten val, recursively
        if isinstance(val, dict):
            flattened = flatten_dict(val)

            for subkey, subval in flattened.items():
                flattened_key = f"{key}_{subkey}"
                ans[flattened_key] = subval
        else:
            ans[key] = val

    return ans
