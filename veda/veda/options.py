from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class InterpreterOptions:
    safe_mode: bool = False
    allowed_roots: list[Path] = field(default_factory=list)

    def normalized_roots(self) -> list[Path]:
        roots = self.allowed_roots or [Path.cwd()]
        out: list[Path] = []
        for r in roots:
            try:
                out.append(Path(r).resolve())
            except Exception:
                out.append(Path(r))
        return out

