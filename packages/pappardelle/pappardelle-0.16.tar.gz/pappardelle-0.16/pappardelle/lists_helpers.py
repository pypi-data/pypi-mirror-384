def lookup_lists(list1, list2, match_check=lambda x, y: x == y):  # left outer join
    """
    Joins two lists based on a match condition
    :param list1: Base list
    :param list2: Lookup list
    :param match_check: Lambda with 2 arguments to match the elements between the two lists
    :return: A list containing a dictionary with "base" and "lookup"
    """
    result = []
    for iter1 in list1:
        matching_iter2 = None
        for iter2 in list2:
            if match_check(iter1, iter2):
                matching_iter2 = iter2
                break
        result.append({'base': iter1, 'lookup': matching_iter2})
    return result


def compare_lists(list1, list2, equal_check=lambda x, y: x == y):
    """
    Compares two lists and returns the diff
    :param list1: First list
    :param list2: Second list
    :param equal_check: Optional, Lambda with 2 arguments to compare the elements of the two lists
    :return: A dictionary containing the keys +, -, =
    """
    result = {
        '=': [],
        '+': [],
        '-': []
    }
    for iter1 in list1:
        is_iter1_found_in_iter2 = False
        for iter2 in list2:
            if equal_check(iter1, iter2):
                is_iter1_found_in_iter2 = True
                break
        if is_iter1_found_in_iter2:
            result['='].append(iter1)
        else:
            result['+'].append(iter1)
    for iter2 in list2:
        is_iter2_found_in_iter1 = False
        for iter1 in list1:
            if equal_check(iter1, iter2):
                is_iter2_found_in_iter1 = True
                break
        if not is_iter2_found_in_iter1:
            result['-'].append(iter2)
    return result


def list_first(a_list):
    """
    Extracts the first list element
    :param a_list: A list
    :return: The first list element
    """
    if a_list is None:
        return None

    tmp_list = list(a_list)  # In case we have a filter result instead of an actual list
    if len(tmp_list) == 0:
        return None

    return tmp_list[0]

