"""Internal compatibility helpers for third-party dependencies."""

from __future__ import annotations

import inspect
from typing import Any, Callable

try:
    import pydantic
except ImportError:  # pragma: no cover
    pydantic = None  # type: ignore[assignment]

_ConstrCallable = Callable[..., Any]

if pydantic is None:  # pragma: no cover
    def constr(*args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
        raise RuntimeError("pydantic is required but not installed")
else:
    _original_constr: _ConstrCallable = pydantic.constr
    try:
        _signature = inspect.signature(_original_constr)
    except (TypeError, ValueError):  # pragma: no cover
        _signature = None

    if _signature is None or "regex" in _signature.parameters:
        constr = _original_constr
    else:

        def constr(*args: Any, **kwargs: Any) -> Any:  # type: ignore[override]
            if "regex" in kwargs:
                kwargs["pattern"] = kwargs.pop("regex")
            return _original_constr(*args, **kwargs)

__all__ = ("constr",)
