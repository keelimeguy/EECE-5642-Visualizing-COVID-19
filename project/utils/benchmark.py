"""
by Keelin Becker-Wheeler, Mar 2020
"""

import time


def benchmark_timing(description, func, *args, **kwargs):
    """ Calls a given function and prints how long its execution took

    :param description: Descriptor that will be printed before timing begins
    :param func: The function that will be timed
    :param *args: Arguments that will be passed to the given function
    :param **kwargs: Keyword arguments that will be passed to the given function

    :type description: str

    :returns: The value as returned by func(*args, **kwargs)
    """

    print(f"{description}..", flush=True, end=' ')
    start = time.time()

    # Run the function and save return value
    ret = func(*args, **kwargs)

    end = time.time()
    print(f"{end-start:0.4f}s", flush=True)

    return ret
