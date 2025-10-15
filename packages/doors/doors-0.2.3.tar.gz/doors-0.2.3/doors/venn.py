""" analysis """
import itertools
from collections import OrderedDict

# pylint: disable=invalid-name


def get_venn_values(df, group_col, id_col):
    all_elements_for_each_venn_group = get_elements_for_each_combination(
        df, group_col, id_col
    )
    venn_values = get_venn_elements_from_interactions(all_elements_for_each_venn_group)
    return venn_values


def get_elements_for_each_combination(df, group_col, id_col):
    """
    for a given df, and group columns, get the intersections
    based in an id column
    """

    def get_ids_for_combination(combination):
        """
        for a given list of elements get the ids in the DF
        """
        ids_in = []
        for element in combination:
            ids_in.append(set(df.loc[df[group_col] == element, id_col]))
        ids_in_intersection = set.intersection(*ids_in)
        return ids_in_intersection

    venn_group_ids = sorted(list(df[group_col].unique()))
    venn_data_by_levels = get_all_combinations(venn_group_ids)
    result = OrderedDict()
    for venn_level in venn_data_by_levels:
        for element in venn_level:
            element_in_level = set(element)
            result[element] = get_ids_for_combination(element_in_level)
    return result


def get_all_combinations(elements):
    """get all combinations for a venn diagram from a list of elements"""
    result = []
    n = len(elements)
    for i in range(n):
        idx = n - i
        result.append(list(set(itertools.combinations(elements, idx))))
    return result


def get_venn_elements_from_interactions(all_intersections):
    """filter out duplicated elements within intersections
    to build the venn diagram elements"""

    def filter_elements(int_name, elements, other_intersections):
        elements_in_other_intersections = []
        for other_int_name, other_elements in other_intersections.items():
            for key in int_name:
                if key in other_int_name:
                    elements_in_other_intersections.append(other_elements)
        result = elements.difference(*elements_in_other_intersections)
        return result

    # assumes intersections are sorted from center to outside of the venn diag.
    assert len(list(all_intersections.keys())[0]) > len(
        list(all_intersections.keys())[-1]
    )
    result = OrderedDict()
    reversed_intersections = OrderedDict(reversed(list(all_intersections.items())))
    other_intersections = reversed_intersections.copy()
    for intersection, elements in reversed_intersections.items():
        del other_intersections[intersection]
        filtered_elements = filter_elements(intersection, elements, other_intersections)
        result[intersection] = filtered_elements
    result_original_order = OrderedDict(reversed(list(result.items())))
    return result_original_order
