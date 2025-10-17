import concurrent.futures
import logging
import functools

from typing import List
from aceutils.logger import LoggingAdapter

logger = logging.getLogger(__name__)
log = LoggingAdapter(logger)


def get_parallelization_groups(objects: list, max_number_of_threads: int) -> List[List]:
    """
    Split list of objects into n sublists of preferably same length - with n being the number of threads.
    The number of threads n is either the input parameter max_number_of_threads or the number of objects.
    """
    n_objects = len(objects)

    if max_number_of_threads > n_objects:
        number_of_threads = n_objects
    else:
        number_of_threads = max_number_of_threads

    if not number_of_threads==0:
        k, m = divmod(n_objects, number_of_threads)
        object_groups = [
            objects[i * k + min(i, m) : (i + 1) * k + min(i + 1, m)]
            for i in range(number_of_threads)
        ]
    else:
        object_groups=[]

    return object_groups, number_of_threads

def execute_func_in_parallel(function, objects: list, max_number_of_threads: int, *function_args) -> list:
    """
    Execute a function in parallel. Takes list of objects as input and splits it in object_groups of preferably equal length.
    The number of threads is equal to the number of object_groups.
    If the function has arguments they can be passed as additional arguments.
    """
    object_groups, number_of_threads = get_parallelization_groups(objects=objects, max_number_of_threads=max_number_of_threads)
    
    log.info(f"Parallelization of function '{function.__name__ }' with number of threads: {number_of_threads}")

    result_groups = []
    if number_of_threads>0:
        with concurrent.futures.ThreadPoolExecutor(max_workers=number_of_threads) as pool:
            partial_function = functools.partial(function, *function_args)
            for result_group in pool.map(partial_function, object_groups):
                if result_group:
                    result_groups.extend(result_group)
    return result_groups