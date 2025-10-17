import functools
import typing

__all__ = ["hooks"]


def hooks(pre: typing.Callable = None, post: typing.Callable = None):
    """
    Decorator to add optional pre and post hook methods to a function.

    Args:
        pre (Callable): Function to run before the main function.
        post (Callable): Function to run after the main function.

    Returns:
        Callable: The decorated function.
    """

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if pre:
                pre(*args, **kwargs)
            result = func(*args, **kwargs)
            if post:
                post(result, *args, **kwargs)
            return result

        return wrapper

    return decorator
