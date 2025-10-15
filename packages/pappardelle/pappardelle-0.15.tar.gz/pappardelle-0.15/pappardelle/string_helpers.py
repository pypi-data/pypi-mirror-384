def string_or_default(*args):
    retVal = None
    for iter in args:
        if is_null_or_whitespace(retVal):
            retVal = iter
        else:
            break
    return retVal

def is_null_or_whitespace(val):
    return val is None or (type(val) == str and val.strip() == '')

def is_null_or_empty(val):
    return val is None or val == ''

def str_ignorecase_equals(str1, str2):
    return str1.upper() == str2.upper()

def str_ignorecase_index(str1, str2):
    return str1.upper().index(str2.upper())

def str_ignorecase_startswith(str1, str2):
    return str1.upper().startswith(str2.upper())

def if_whitespace_make_null(a_str):
    return a_str if not is_null_or_whitespace(a_str) else None
