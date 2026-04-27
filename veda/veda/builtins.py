from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional

from veda.errors import SourceSpan, VedaTypeError


def veda_type_name(value: Any) -> str:
    if value is None:
        return "none"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "text"
    if isinstance(value, list):
        return "list"
    if isinstance(value, dict):
        return "map"
    if isinstance(value, set):
        return "set"
    if isinstance(value, (bytes, bytearray)):
        return "bytes"
    if isinstance(value, datetime):
        return "datetime"
    if hasattr(value, "__class__") and value.__class__.__name__ == "VedaModule":
        return "module"
    if callable(value):
        return "function"
    return "unknown"


def to_veda_text(value: Any) -> str:
    if value is None:
        return "none"
    if value is True:
        return "true"
    if value is False:
        return "false"
    if isinstance(value, list):
        inner = ", ".join(to_veda_text(v) for v in value)
        return "[" + inner + "]"
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(f"{k}: {to_veda_text(v)}")
        return "{" + ", ".join(parts) + "}"
    if isinstance(value, set):
        inner = ", ".join(to_veda_text(v) for v in list(value))
        return "set([" + inner + "])"
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


@dataclass(frozen=True)
class BuiltinFunction:
    name: str
    impl: Callable[[list[Any], str, SourceSpan], Any]
    min_arity: int
    max_arity: Optional[int] = None

    def call(self, args: list[Any], *, source: str, span: SourceSpan) -> Any:
        if len(args) < self.min_arity:
            raise VedaTypeError(
                f"{self.name}() expected at least {self.min_arity} argument(s), got {len(args)}.",
                source=source,
                span=span,
            )
        if self.max_arity is not None and len(args) > self.max_arity:
            raise VedaTypeError(
                f"{self.name}() expected at most {self.max_arity} argument(s), got {len(args)}.",
                source=source,
                span=span,
            )
        return self.impl(args, source, span)

    def __repr__(self) -> str:
        return f"<builtin {self.name}>"
