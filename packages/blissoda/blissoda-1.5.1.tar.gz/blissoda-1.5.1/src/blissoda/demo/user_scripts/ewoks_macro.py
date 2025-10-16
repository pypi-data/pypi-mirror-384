import inspect
import typing

from blissoda.demo import testing
from blissoda.demo.processors.ewoks_macro import DemoEwoksMacroHandler

ewoks_macro_handler = DemoEwoksMacroHandler()


def ewoks_macro_demo():
    test_ewoks_macro_list()
    test_ewoks_macro_load_and_execute()
    test_ewoks_macro_arguments()


@testing.integration_fixture
def _ewoks_macro_handler():
    rootdir = ewoks_macro_handler.user_script_homedir()
    file1 = rootdir / "file1.py"
    file2 = rootdir / "subdir1" / "file2.py"
    file3 = rootdir / "file3.py"

    file2.parent.mkdir(parents=True, exist_ok=True)

    file1.write_text(_REMOTE_FILE1)
    file2.write_text(_REMOTE_FILE2)
    file3.write_text(_REMOTE_FILE3)

    yield ewoks_macro_handler


_REMOTE_FILE1 = '''
def func_with_docstring(n):
    """Doc string func_with_docstring"""
    return list(range(n))
'''

_REMOTE_FILE2 = """
from typing import List

def func_with_annotations(n:int=4) -> List:
    return list(range(n))
"""


_REMOTE_FILE3 = """
from typing import List, Tuple, Optional, Any, Dict

def func_many_types(
    a: int,
    b: str,
    /,                  # <-- positional-only up to here
    c: bool,
    d: float,
    *args: int,         # <-- after this, only keyword args allowed
    e: Tuple[int] = (1, 2, 3),
    f: Optional[str] = None,
    g: List[int] = [42],
    **kwargs: int
) -> Dict[str, Any]:
    return {
        'a': a,
        'b': b,
        'c': c,
        'd': d,
        'e': e,
        'f': f,
        'g': g,
        'args': args,
        'kwargs': kwargs
    }
"""


@testing.integration_test
def test_ewoks_macro_list(_ewoks_macro_handler):
    _, files = _ewoks_macro_handler._user_script_list()
    base_names = {filepath.name for filepath in files}
    expected = {"file1.py", "file2.py", "file3.py"}
    assert base_names == expected, base_names


@testing.integration_test
def test_ewoks_macro_load_and_execute(_ewoks_macro_handler):
    ns1 = _ewoks_macro_handler.user_script_load(
        "file1.py", export_global=False, blocking=True, timeout=10
    )
    result1 = ns1.func_with_docstring(3)
    assert result1 == [0, 1, 2], result1

    ns2 = _ewoks_macro_handler.user_script_load(
        "subdir1/file2.py", export_global=False, blocking=True, timeout=10
    )
    result2 = ns2.func_with_annotations()
    assert result2 == [0, 1, 2, 3], result2

    ns1.func_with_docstring.__doc__ == "Doc string func_with_docstring"
    ns2.func_with_annotations.__doc__.startswith(
        "Ewoks proxy for function 'func_with_annotations' in file '"
    )
    ns2.func_with_annotations.__doc__.endswith("file2.py'")


@testing.integration_test
def test_ewoks_macro_arguments(_ewoks_macro_handler):
    ns = _ewoks_macro_handler.user_script_load(
        "file3.py", export_global=False, blocking=True, timeout=10
    )

    args = ([-1], -2)
    kwargs = {"extra": -3}
    result = ns.func_many_types(
        42, "hello", False, 2.71, *args, f="world", g=[4, 5, 6], **kwargs
    )

    expected = {
        "a": 42,
        "b": "hello",
        "c": False,
        "d": 2.71,
        "e": (1, 2, 3),
        "f": "world",
        "g": [4, 5, 6],
        "args": args,
        "kwargs": kwargs,
    }
    assert result == expected, result

    sig = inspect.signature(ns.func_many_types)
    param_a = sig.parameters["a"]
    param_e = sig.parameters["e"]
    param_g = sig.parameters["g"]
    type_e = param_e.annotation.__origin__
    type_g = param_g.annotation.__origin__
    type_return = sig.return_annotation.__origin__
    assert param_a.annotation is int, param_a.annotation
    assert param_e.default == (1, 2, 3), param_e.default
    assert type_e in (tuple, typing.Tuple), type_e
    assert type_g in (list, typing.List), type_g
    assert type_return in (dict, typing.Dict), type_return
