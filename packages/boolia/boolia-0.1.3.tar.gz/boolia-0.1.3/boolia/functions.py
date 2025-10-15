from typing import Any, Callable, Dict
import re


class FunctionRegistry:
    def __init__(self):
        self._fns: Dict[str, Callable[..., Any]] = {}

    def register(self, name: str, fn: Callable[..., Any]) -> None:
        if not isinstance(name, str) or not name:
            raise ValueError("Function name must be a non-empty string")
        self._fns[name] = fn

    def get(self, name: str) -> Callable[..., Any]:
        fn = self._fns.get(name)
        if fn is None:
            raise NameError(f"Unknown function: {name}")
        return fn


DEFAULT_FUNCTIONS = FunctionRegistry()

# Built-ins
DEFAULT_FUNCTIONS.register("len", lambda x: len(x) if x is not None else 0)
DEFAULT_FUNCTIONS.register("starts_with", lambda s, p: str(s).startswith(str(p)))
DEFAULT_FUNCTIONS.register("ends_with", lambda s, suf: str(s).endswith(str(suf)))
DEFAULT_FUNCTIONS.register("contains", lambda container, item: (item in container) if hasattr(container, "__contains__") else False)
DEFAULT_FUNCTIONS.register("matches", lambda s, pat: re.fullmatch(str(pat), str(s)) is not None)
