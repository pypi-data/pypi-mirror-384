import functools
import inspect
import pathlib
from contextlib import ExitStack
from contextlib import contextmanager
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple

_DEMO_FIXTURE_REGISTRY: Dict[str, Callable[..., Generator[Any, None, None]]] = {}
_DEMO_FIXTURE_AUTOUSE: List[Callable[..., Generator[Any, None, None]]] = []


def integration_fixture(
    arg: Optional[Callable[..., Any]] = None, **kwargs
) -> Callable[..., Generator[Any, None, None]]:
    """Can be used like `pytest.fixture` with the 'function' scope."""
    if arg is not None and callable(arg) and not kwargs:
        # @integration_fixture
        return _register_fixture(arg)
    elif arg is None:
        # @integration_fixture(...)
        def wrapper(
            fixture: Callable[..., Any],
        ) -> Callable[..., Generator[Any, None, None]]:
            return _register_fixture(fixture, **kwargs)

        return wrapper
    else:
        raise TypeError(
            "@integration_fixture must be used as @integration_fixture or @integration_fixture()"
        )


def _register_fixture(
    fixture: Callable[..., Any], autouse: bool = False
) -> Callable[..., Generator[Any, None, None]]:
    """Ensure `integration_test` can find the fixture. Handle fixture functions and context managers.
    Cache fixture results within the scope of a single function.
    """
    if not callable(fixture):
        raise TypeError(
            f"@integration_fixture can only decorate callables, got {type(fixture).__name__}"
        )

    # Allow reloading the same fixture
    test_arg_name = fixture.__name__
    unique_name = _function_id(fixture)
    existing_final_fixture, existing_unique_name = _DEMO_FIXTURE_REGISTRY.get(
        test_arg_name, (None, None)
    )
    if existing_final_fixture and unique_name != existing_unique_name:
        raise RuntimeError(
            f"A fixture with name {test_arg_name!r} already exists: {unique_name!r}"
        )

    result_cache = []

    @contextmanager
    def _clear_cache_ctx():
        try:
            yield
        finally:
            result_cache.clear()

    if inspect.isgeneratorfunction(fixture):

        @functools.wraps(fixture)
        @contextmanager
        def fixture_ctx(*args, **kwargs) -> Generator[Any, None, None]:
            gen = fixture(*args, **kwargs)
            try:
                yield next(gen)
            finally:
                # Ensure fixture teardown is always called (pytest behavior)
                try:
                    next(gen)
                except StopIteration:
                    pass

    else:

        @functools.wraps(fixture)
        @contextmanager
        def fixture_ctx(*args, **kwargs) -> Generator[Any, None, None]:
            yield fixture(*args, **kwargs)

    @functools.wraps(fixture_ctx)
    @contextmanager
    def wrapped_fixture(*args, **kwargs) -> Generator[Any, None, None]:
        with ExitStack() as stack:
            final_args, final_kwargs = _resolve_fixture_arguments(
                fixture, stack, args=args, kwargs=kwargs
            )
            if result_cache:
                result = result_cache[0]
            else:
                result = stack.enter_context(fixture_ctx(*final_args, **final_kwargs))
                result_cache.append(result)
                _ = stack.enter_context(_clear_cache_ctx())
            yield result

    _DEMO_FIXTURE_REGISTRY[test_arg_name] = wrapped_fixture, unique_name
    if autouse:
        _DEMO_FIXTURE_AUTOUSE.append(wrapped_fixture)

    return wrapped_fixture


def _resolve_fixture_arguments(
    fn: Callable[..., Any],
    stack: ExitStack,
    args: Tuple[Any, ...] = (),
    kwargs: Optional[Dict[str, Any]] = None,
) -> Tuple[Tuple[Any, ...], Dict[str, Any]]:
    """Resolve fixture arguments"""
    if kwargs is None:
        kwargs = {}

    sig = inspect.signature(fn)
    bound = sig.bind_partial(*args, **kwargs)
    bound.apply_defaults()

    positional_args: List[Any] = []
    keyword_args: Dict[str, Any] = {}

    for param in sig.parameters.values():
        if param.kind in (
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
        ):
            if param.name in bound.arguments:
                val = bound.arguments[param.name]
            elif param.name in _DEMO_FIXTURE_REGISTRY:
                fixture, _ = _DEMO_FIXTURE_REGISTRY[param.name]
                val = stack.enter_context(fixture())
            else:
                raise TypeError(
                    f"Missing required argument '{param.name}' for {fn.__name__!r}"
                )

            positional_args.append(val)

        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            if param.name in bound.arguments:
                val = bound.arguments[param.name]
            elif param.name in _DEMO_FIXTURE_REGISTRY:
                fixture, _ = _DEMO_FIXTURE_REGISTRY[param.name]
                val = stack.enter_context(fixture())
            else:
                raise TypeError(
                    f"Missing required keyword argument '{param.name}' for {fn.__name__!r}"
                )

            keyword_args[param.name] = val

        elif param.kind == inspect.Parameter.VAR_POSITIONAL:
            # pass all remaining user-provided positional args
            positional_args.extend(args[len(positional_args) :])

        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            # include remaining user-provided kwargs
            keyword_args.update(
                {k: v for k, v in kwargs.items() if k not in keyword_args}
            )
            # include all remaining fixtures that are not already included
            for name, (fixture, _) in _DEMO_FIXTURE_REGISTRY.items():
                if name not in keyword_args:
                    keyword_args[name] = stack.enter_context(fixture())

    return tuple(positional_args), keyword_args


def _function_id(fn: Callable[..., Any]) -> str:
    filename = pathlib.Path(fn.__code__.co_filename).resolve()
    cwd = pathlib.Path.cwd().resolve()
    try:
        location = str(filename.relative_to(cwd))
    except ValueError:
        location = fn.__module__
    qualname = "::".join(fn.__qualname__.split("."))
    return f"{location}::{qualname}"
