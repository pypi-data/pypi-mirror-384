from datetime import datetime

def exec_time(func_arg):
    """
    Prints the execution time for a function
    :param func_arg:
    :return:
    """
    def inner_exec_time():
        dt1 = datetime.now()
        func_arg()
        dt2 = datetime.now()
        print(f"{func_arg.__name__} ran in {dt2 - dt1}")
    return inner_exec_time


class CacheOrLambda:
    my_cache = {}
    my_lambda = None

    def __init__(self, a_lambda):
        self.my_lambda = a_lambda

    def fetch(self, a_key):
        retVal = None
        if a_key in self.my_cache:
            retVal = self.my_cache[a_key]
        else:
            retVal = self.my_lambda(a_key)
            self.my_cache[a_key] = retVal
        return retVal
