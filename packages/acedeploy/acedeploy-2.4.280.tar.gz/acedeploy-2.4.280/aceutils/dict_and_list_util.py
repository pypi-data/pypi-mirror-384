from typing import  Dict, Tuple
import copy

def compare_dicts(dict1, dict2):
    """
    Compare two dictionaries. Dictionaries may only contain hashable types.
    Return set of two dictionaries.
    First dictionary contains all items only in first input dictionary.
    Second dictionary contains all items only in second input dictionary.
    """
    set1 = set(dict1.items())
    set2 = set(dict2.items())
    only_in_dict1 = dict(set1 - set2)
    only_in_dict2 = dict(set2 - set1)
    return only_in_dict1, only_in_dict2


def compare_nested_dicts(dict1, dict2) -> Tuple[Dict,Dict]:
    """
    Compare two nested dictionaries - only one sublayer supported. Dictionaries may only contain hashable types or "non-nested"-dictionaries.
    Return two nested dictionaries.
    First nested dictionary contains all items only in first input nested dictionary.
    Second nested dictionary contains all items only in second input nested dictionary.
    """
    dict1_sub_diffs={}
    dict2_sub_diffs={}

    dict1_copy=copy.deepcopy(dict1)
    dict2_copy=copy.deepcopy(dict2)

    for key, value in dict1_copy.items():
        if type(value) is dict and key not in dict2_copy:
            dict1_sub_diffs[key]=value
            dict1.pop(key)
        elif type(value) is dict and type(dict2_copy[key]) is not dict:
            raise ValueError(f"Nested dictionaries don't have the same structure.")
        elif type(value) is dict and type(dict2_copy[key]) is dict:
            sub_dict_1=dict1.pop(key)
            sub_dict_2=dict2.pop(key)

            only_in_sub_dict1, only_in_sub_dict2 = compare_dicts(sub_dict_1, sub_dict_2)

            if only_in_sub_dict1:
                dict1_sub_diffs[key]=only_in_sub_dict1
            if only_in_sub_dict2:
                dict2_sub_diffs[key]=only_in_sub_dict2

    for key, value in dict2_copy.items():
        if type(value) is dict and key not in dict1_copy:
            dict2_sub_diffs[key]=value
            dict2.pop(key)
        elif type(value) is dict and type(dict1_copy[key]) is not dict:
            raise ValueError(f"Nested dictionaries don't have the same structure.")

    only_in_dict1, only_in_dict2 = compare_dicts(dict1, dict2)
    only_in_dict1 |= dict1_sub_diffs 
    only_in_dict2 |= dict2_sub_diffs 
    return only_in_dict1, only_in_dict2

def strip_nested_dict(d):
    """
    Remove empty entries from a (nested) dictioary.
    Entries count as empty if they are one of ('', None, [], {}).
    """
    result = {}
    for k, v in d.items():
        if isinstance(v, dict):
            v = strip_nested_dict(v)
        if v not in ("", None, [], {}):
            result[k] = v
    return result


def list_casefold(string_list):
    """
    Given a list of string, apply casefold() to each of them.
    If the input is a Null value, return empty list.
    """
    if string_list:
        return [s.casefold() for s in string_list]
    else:
        return []


def list_upper(string_list):
    """
    Given a list of string, apply upper() to each of them.
    If the input is a Null value, return empty list.
    """
    if string_list:
        return [s.upper() for s in string_list]
    else:
        return []


def list_lower(string_list):
    """
    Given a list of string, apply lower() to each of them.
    If the input is a Null value, return empty list.
    """
    if string_list:
        return [s.lower() for s in string_list]
    else:
        return []


def flatten(nested_list):
    """
    Flatten arbitrary nested lists
    """
    result = []
    if isinstance(nested_list, (list, tuple)):
        for x in nested_list:
            result.extend(flatten(x))
    else:
        result.append(nested_list)
    return result


def chunks(lst, n):
    """
    Yield successive n-sized chunks from lst.
    """
    for i in range(0, len(lst), n):
        yield lst[i : i + n]

def list_to_string_representation(lst) -> str:
    """
    Transforms a list to a string representation which can, for example, be used in Snowflake.
    E.g. ["a","b"] -> "'a','b'"
    """
    result = ", ".join(
        [f"'{s}'" for s in lst]
    )
    return result

def list_ends_with_list(list_a, list_b):
    """
    Check if list A ends with entries given in list B.
    If list B is empty, return True.
    If list B is longer than list A, return False.
    """
    if len(list_b) == 0:
        return True
    if len(list_b) > len(list_a):
        return False
    return list_a[-len(list_b):] == list_b
