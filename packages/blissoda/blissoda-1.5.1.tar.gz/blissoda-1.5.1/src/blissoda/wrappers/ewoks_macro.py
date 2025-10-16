import ast
import inspect
import os
import typing as _typing
from pathlib import Path
from typing import Any
from typing import Callable
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from esrf_pathlib import ESRFPath
from ewoksjob import client

from ..bliss_globals import current_session
from ..import_utils import unavailable_class

try:
    from bliss.common.utils import UserNamespace
except ImportError as ex:
    UserNamespace = unavailable_class(ex)


from ..persistent.parameters import ParameterInfo
from ..processor import BaseProcessor


class EwoksMacroHandler(
    BaseProcessor, parameters=[ParameterInfo("queue", category="workflows")]
):
    """Ewoks macro's are the equivalent of Bliss macro's with the difference
    that the functions are executed remotely via Ewoks.
    """

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        if defaults is None:
            defaults = {}
        defaults.setdefault("queue", "user")
        super().__init__(config, defaults)

    def _info_categories(self) -> Dict[str, dict]:
        categories = super()._info_categories()
        scripts = categories.setdefault("Remote scripts", {})
        scripts["Location"] = self.user_script_homedir()
        scripts["#scripts"] = len(self._user_script_list()[1])
        return categories

    def user_script_homedir(self) -> ESRFPath:
        """Root directory for scripts with relative file paths.

        Equivalent of ``user_script_homedir`` from Bliss for local Bliss macro's.
        """
        dataset_filename = ESRFPath(current_session.scan_saving.filename)
        return dataset_filename.scripts_path

    def user_script_load(
        self,
        scriptname: str,
        export_global: Union[str, bool] = "ewoks",
        blocking: bool = False,
        timeout: Optional[float] = None,
    ) -> Optional[UserNamespace]:
        """
        Parse a script to extract function definitions and expose them
        as Ewoks function proxies in the Bliss session's ``env_dict``.

        Each proxy builds a one-node Ewoks workflow dict and submits it.

        Equivalent of ``user_script_load`` from Bliss for local Bliss macro's.

        :param scriptname: The python file to load (absolute path or relative to ``user_script_homedir``).
        :param export_global: Where to install the functions:
                            - ``True``: inject into global session namespace ``env_dict``
                            - "namespace" (`default="ewoks"`): inject into that namespace
                            - ``False``: return a UserNamespace instead of injecting
        :param blocking: Wait for result.
        :param timeout: Timeout when waiting for the result.
        :returns: If ``export_global`` is ``False``, returns a ``UserNamespace`` containing function proxies.
                  Otherwise, functions are injected into the session ``env_dict`` and nothing is returned.
        """
        if not scriptname:
            self._user_script_list()
            return

        filepath = self._resolve_filepath(scriptname)
        function_proxies = self._create_function_proxies(
            filepath, blocking=blocking, timeout=timeout
        )

        if export_global is True:
            current_session._update_env_dict_from_globals_dict(function_proxies)
            return None

        if isinstance(export_global, str):
            ns_name = export_global
            env_dict = current_session.env_dict
            if isinstance(env_dict.get(ns_name), UserNamespace):
                env_dict[ns_name] = env_dict[ns_name] + function_proxies
                print(f"Merged [{ns_name}] namespace in session.")
            else:
                if ns_name in env_dict:
                    print(f"Replaced [{ns_name}] in session env")
                env_dict[ns_name] = UserNamespace(**function_proxies)
                print(f"Exported [{ns_name}] namespace in session.")
            return None

        return UserNamespace(**function_proxies)

    def user_script_list(self):
        """List python scripts from the proposal SCRIPTS directory.

        Equivalent of ``user_script_list`` from Bliss for local Bliss macro's.
        """
        rootdir, files = self._user_script_list()
        print(f"List of python files for remote execution in [{rootdir}]:")
        for scriptname in files:
            print(f" - {scriptname}")

    def _user_script_list(self) -> Tuple[ESRFPath, List[Path]]:
        rootdir = self.user_script_homedir()
        if not rootdir.is_dir():
            return rootdir, []

        files = []
        for dirpath, dirnames, filenames in os.walk(rootdir):
            dirpath = Path(dirpath).relative_to(rootdir)
            for filename in filenames:
                _, ext = os.path.splitext(filename)
                if ext != ".py":
                    continue
                files.append(Path(dirpath) / filename)
        return rootdir, files

    def _resolve_filepath(self, scriptname: str) -> Path:
        """Resolve a scriptname to an absolute Python file path."""
        if not scriptname.endswith(".py"):
            scriptname += ".py"

        if os.path.isabs(scriptname):
            filepath = Path(scriptname)
        else:
            filepath = self.user_script_homedir() / scriptname

        if not filepath.is_file():
            raise RuntimeError(f"Cannot find [{filepath}] !")

        return filepath

    def _create_function_proxies(
        self,
        filepath: Path,
        blocking: bool = False,
        timeout: Optional[float] = None,
    ) -> Dict[str, Callable[..., Any]]:
        """Parse a Python file and return proxies for all public top-level functions."""
        if not filepath.is_absolute():
            raise ValueError(f"File path must be absolute [{filepath}]")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            raise RuntimeError(f"Failed to read file [{filepath}]: {e!r}") from e

        try:
            tree = ast.parse(source, filename=filepath)
        except SyntaxError as e:
            raise RuntimeError(
                f"Syntax error while parsing [{filepath}]: {e.msg} (line {e.lineno})"
            ) from e

        function_proxies = {}

        for node in tree.body:
            if not isinstance(node, ast.FunctionDef) or node.name.startswith("_"):
                continue
            func_name = node.name
            docstring = ast.get_docstring(node)
            signature = _create_function_signature(node)
            function_proxies[func_name] = self._create_function_proxy(
                filepath,
                func_name,
                signature,
                docstring,
                blocking=blocking,
                timeout=timeout,
            )

        return function_proxies

    def _create_function_proxy(
        self,
        filepath: Path,
        func_name: str,
        signature: inspect.Signature,
        doc: Optional[str],
        blocking: bool = False,
        timeout: Optional[float] = None,
    ) -> Callable[..., Any]:
        """Create a function proxy with a specific signature."""

        def wrapper(*args, **kwargs) -> Any:
            remote_function_url = f"{filepath}::{func_name}"
            workflow = {
                "graph": {"id": f"workflow_{func_name}"},
                "nodes": [
                    {
                        "id": "main",
                        "task_type": "method",
                        "task_identifier": remote_function_url,
                    }
                ],
                "links": [],
            }

            inputs = _workflow_inputs_from_signature(signature, args, kwargs)

            try:
                future = client.submit(
                    args=(workflow,), kwargs={"inputs": inputs}, queue=self.queue
                )
            except Exception as exc:
                raise RuntimeError(f"Failed to submit Ewoks job: {exc!r}") from exc

            if not blocking:
                return _Future(future.uuid)
            result = future.result(timeout=timeout)
            return _parse_future_result(result)

        wrapper.__name__ = func_name
        wrapper.__signature__ = signature
        wrapper.__doc__ = (
            doc or f"Ewoks proxy for function {func_name!r} in file {str(filepath)!r}"
        )
        return wrapper


class _Future(client.Future):
    def result(self, *args, **kwargs) -> Any:
        result = super().result(*args, **kwargs)
        return _parse_future_result(result)


def _parse_future_result(result: Any) -> Any:
    if isinstance(result, dict) and "return_value" in result:
        return result["return_value"]
    return result


def _workflow_inputs_from_signature(
    signature: inspect.Signature, args: tuple, kwargs: dict
) -> List[dict]:
    bound = signature.bind_partial(*args, **kwargs)

    # We could fill in the defaults but their evaluation might have failed
    # so let the remote do handle defaults.
    # bound.apply_defaults()

    inputs = []

    has_positional_vars = any(
        p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.POSITIONAL_ONLY)
        for p in signature.parameters.values()
    )

    idx = 0
    for name, param in signature.parameters.items():
        if name not in bound.arguments:
            continue
        value = bound.arguments[name]

        if param.kind == inspect.Parameter.VAR_POSITIONAL:
            for v in value:
                inputs.append({"name": idx, "value": v})
                idx += 1
        elif param.kind == inspect.Parameter.VAR_KEYWORD:
            for k, v in value.items():
                inputs.append({"name": k, "value": v})
        elif param.kind == inspect.Parameter.POSITIONAL_ONLY:
            inputs.append({"name": idx, "value": value})
            idx += 1
        elif param.kind == inspect.Parameter.KEYWORD_ONLY:
            inputs.append({"name": name, "value": value})
        elif param.kind == inspect.Parameter.POSITIONAL_OR_KEYWORD:
            if has_positional_vars:
                inputs.append({"name": idx, "value": value})
                idx += 1
            else:
                inputs.append({"name": name, "value": value})

    return inputs


def _create_function_signature(node: ast.FunctionDef) -> inspect.Signature:
    """Create a function signature from an ``ast.FunctionDef`` node.

    Handles:
      - normal args
      - positional-only args (if present)
      - keyword-only args
      - varargs and kwargs
      - default value fallback
      - annotation eval attempt (safe)
    """
    params: List[inspect.Parameter] = []

    posonly = getattr(node.args, "posonlyargs", []) or []
    regular_args = node.args.args or []
    kwonly_args = node.args.kwonlyargs or []
    defaults = node.args.defaults or []
    kw_defaults = node.args.kw_defaults or []

    # Build defaults aligner for regular args (posonly + regular)
    regular_all = list(posonly) + list(regular_args)
    num_regular = len(regular_all)
    num_defaults = len(defaults)
    defaults_prefix = [None] * (num_regular - num_defaults) + list(defaults)

    # Process positional-only and regular args
    for arg, default_expr in zip(regular_all, defaults_prefix):
        parameter = inspect.Parameter(
            arg.arg,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            default=_eval_default(default_expr),
            annotation=_parse_annotation(arg.annotation),
        )
        params.append(parameter)

    # varargs (*args)
    if node.args.vararg:
        params.append(
            inspect.Parameter(node.args.vararg.arg, inspect.Parameter.VAR_POSITIONAL)
        )

    # keyword-only args
    for arg, default_expr in zip(kwonly_args, kw_defaults):
        parameter = inspect.Parameter(
            arg.arg,
            inspect.Parameter.KEYWORD_ONLY,
            default=_eval_default(default_expr),
            annotation=_parse_annotation(arg.annotation),
        )
        params.append(parameter)

    # kwargs (**kwargs)
    if node.args.kwarg:
        params.append(
            inspect.Parameter(node.args.kwarg.arg, inspect.Parameter.VAR_KEYWORD)
        )

    return inspect.Signature(params, return_annotation=_parse_annotation(node.returns))


def _parse_annotation(annotation) -> Any:
    if not annotation:
        return inspect.Signature.empty
    try:
        annotation_str = ast.unparse(annotation)
    except Exception:
        return Any
    try:
        return _eval_annotation(annotation_str)
    except Exception:
        # String representation instead of Any so the Bliss REPL completion is informative.
        return annotation_str


def _eval_annotation(annotation_str: str) -> Any:
    safe_builtins = {
        "int": int,
        "float": float,
        "bool": bool,
        "str": str,
        "bytes": bytes,
        "dict": dict,
        "list": list,
        "tuple": tuple,
        "set": set,
        "frozenset": frozenset,
        "object": object,
        "type": type,
        "None": type(None),
    }
    safe_typing = {
        k: getattr(_typing, k) for k in dir(_typing) if not k.startswith("_")
    }
    safe_globals = {
        "__builtins__": {},
        "typing": _typing,
        **safe_builtins,
        **safe_typing,
    }
    return eval(annotation_str, safe_globals, {})


def _eval_default(expr) -> Any:
    if expr is None:
        return inspect.Signature.empty

    try:
        return ast.literal_eval(expr)
    except Exception:
        pass

    try:
        restricted_globals = {"__builtins__": {}}
        return eval(
            compile(ast.Expression(expr), "<ast-default>", "eval"),
            restricted_globals,
            {},
        )
    except Exception:
        pass

    try:
        return ast.unparse(expr)
    except Exception:
        return inspect.Signature.empty
