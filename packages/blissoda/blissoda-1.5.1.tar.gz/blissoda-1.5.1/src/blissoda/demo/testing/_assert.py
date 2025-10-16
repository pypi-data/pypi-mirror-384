import functools
import inspect
import pathlib

from ._display import print_message_on_exit


def demo_assert(message: str):
    if not isinstance(message, str):
        raise TypeError(f"{message} is not a string")

    def decorator(test_method):
        @functools.wraps(test_method)
        def wrapper(*args, **kwargs):
            bound_args = inspect.signature(test_method).bind(*args, **kwargs)
            bound_args.apply_defaults()
            arguments = {
                k: repr(str(v)) if isinstance(v, (pathlib.Path, str)) else v
                for k, v in bound_args.arguments.items()
            }
            msg = message.format(**arguments)

            with print_message_on_exit(msg, "assert"):
                return test_method(*args, **kwargs)

        return wrapper

    return decorator
