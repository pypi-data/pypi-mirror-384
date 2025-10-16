import traceback


def print_exception_trace():
    """
    This method prints the current exception traceback. This method
    is usefull to know more about the problem when we are programming
    and we are manually controlling the exceptions but need to debug.
    """
    print(traceback.format_exc())