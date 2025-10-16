import functools
from contextlib import ExitStack
from typing import Any
from typing import Callable

from ._display import print_message_on_exit
from ._fixtures import _DEMO_FIXTURE_AUTOUSE
from ._fixtures import _function_id
from ._fixtures import _resolve_fixture_arguments


def integration_test(fn: Callable[..., Any]) -> Callable[..., Any]:
    if not callable(fn):
        raise TypeError(f"{fn} is not a callable")

    @functools.wraps(fn)
    def wrapper(*args, **kwargs) -> Any:
        with ExitStack() as stack:
            _enter_autouse_fixtures(stack)
            final_args, final_kwargs = _resolve_fixture_arguments(
                fn, stack, args=args, kwargs=kwargs
            )

            with print_message_on_exit(_function_id(fn), "test"):
                return fn(*final_args, **final_kwargs)

    return wrapper


def _enter_autouse_fixtures(stack: ExitStack) -> None:
    for fixture_ctx in _DEMO_FIXTURE_AUTOUSE:
        stack.enter_context(fixture_ctx())
