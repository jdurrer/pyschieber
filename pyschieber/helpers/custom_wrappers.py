# ----------------------------
# Libraries
# ----------------------------

# Coding support
from functools import wraps
from time import perf_counter
from typing import Callable, Any
import inspect


def debug_wrapper(func: Callable) -> Callable:

    @wraps(func)
    def wrapper(*args, **kwargs):

        # Get the function signature
        sig = inspect.signature(func)
        params = sig.parameters

        args_info = {param: (arg, type(arg)) for param, arg in zip(params, args)}
        kwargs_info = {k: (v, type(v)) for k, v in kwargs.items()}
        print(f"{'#'*33}")
        print(f"{'#'*10} Wrapper Start {'#'*8}")
        print(f"{'#'*33}")
        print(f"Function '{func.__name__}' called with arguments: {args_info} and keyword arguments: {kwargs_info}")
        result = func(*args, **kwargs)
        print(f"Function'{func.__name__}' returned: {result=} (type: {type(result)})")
        print(f"{'#'*33}")
        print(f"{'#'*10} Wrapper End {'#'*10}")
        print(f"{'#'*33}")

        return result
    
    return wrapper


def memoize(func: Callable) -> Callable:
    """Memorizes if the exact same Arguments and Keyword Arguments were entered once before into the same function, resulting to the same output.
    The result will then be presented from memory without the need to rerun the recursive function.

    Args:
        func (Callable): The function that is observed.

    Returns:
        Callable: The result of the observed function.
    """
    cache: dict[str, Any] = {}

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        key: str = str(args) + str(kwargs)

        if key not in cache:
            cache[key] = func(*args, **kwargs)

        return cache[key]
    
    return wrapper


def time_function(func: Callable) -> Callable:

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:

        start_time: float = perf_counter()
        result: Any = func(*args, **kwargs)
        end_time: float = perf_counter()
        print(f'The function {func.__name__} took {end_time-start_time:.2f} seconds to execute.')

        return result
    
    return wrapper