def make_dict_path(a_dict, a_path):
    set_dict_path(a_dict, a_path, {})


def set_dict_path(a_dict, a_path, a_val):
    curr_obj = a_dict
    path_len = len(a_path)
    counter = 0
    for iter_attr in a_path:
        counter += 1
        if counter == path_len:
            curr_obj[iter_attr] = a_val
        if not iter_attr in curr_obj:
            curr_obj[iter_attr] = {}
        curr_obj = curr_obj[iter_attr]


def get_dict_path(a_dict, a_path):
    curr_obj = a_dict
    for iter_attr in a_path:
        if iter_attr in curr_obj:
            curr_obj = curr_obj[iter_attr]
        else:
            return None
    return curr_obj


def deep_copy_dict(a_src, a_dest, overwrite=False):
    for k, v in a_src.items():
        if isinstance(v, dict) and k in a_dest:
            deep_copy_dict(a_src[k], a_dest[k], overwrite)
        else:
            if ((overwrite == True) or (not k in a_dest)):
                a_dest[k] = v


def are_dict_equal(first, second):
    for k, v in first.items():
        iter_are_equal = True
        if isinstance(v, dict) and k in second:
            iter_are_equal = are_dict_equal(v, get_dict_path(second, [k]))
        else:
            iter_are_equal = (v == get_dict_path(second, [k]))
        if not iter_are_equal:
            return False
    for k, v in second.items():
        iter_are_equal = True
        if isinstance(v, dict) and k in first:
            iter_are_equal = are_dict_equal(v, get_dict_path(first, [k]))
        else:
            iter_are_equal = (v == get_dict_path(first, [k]))
        if not iter_are_equal:
            return False
    return True