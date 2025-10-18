from pappardelle import is_null_or_whitespace

def value_or_default(*args):
    retVal = None
    for iter in args:
        if retVal is None or (type(retVal) == str and is_null_or_whitespace(retVal)):
            retVal = iter
        else:
            break
    return retVal
