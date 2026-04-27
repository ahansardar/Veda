from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from veda.errors import SourceSpan, VedaNameError


@dataclass
class Environment:
    values: dict[str, Any]
    enclosing: Optional["Environment"] = None

    def define(self, name: str, value: Any) -> None:
        self.values[name] = value

    def assign(self, name: str, value: Any, *, source: str, span: SourceSpan) -> None:
        if name in self.values:
            self.values[name] = value
            return
        if self.enclosing is not None:
            self.enclosing.assign(name, value, source=source, span=span)
            return
        raise VedaNameError(f"Undefined variable '{name}'.", source=source, span=span)

    def get(self, name: str, *, source: str, span: SourceSpan) -> Any:
        if name in self.values:
            return self.values[name]
        if self.enclosing is not None:
            return self.enclosing.get(name, source=source, span=span)
        raise VedaNameError(f"Undefined variable '{name}'.", source=source, span=span)

