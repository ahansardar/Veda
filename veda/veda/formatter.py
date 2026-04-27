from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FormatResult:
    formatted: str
    changed: bool


def format_source(source: str) -> FormatResult:
    """
    Canonical indentation formatter for Veda.

    - 4 spaces per indent
    - `end` and `else do` align with their block start
    - Leaves triple-quoted strings untouched
    """
    lines = source.splitlines(keepends=False)
    out: list[str] = []

    indent = 0
    in_triple = False

    def has_triple(s: str) -> int:
        return s.count('"""')

    for raw in lines:
        # Preserve exact empty lines.
        if raw.strip() == "":
            out.append("")
            continue

        if has_triple(raw) % 2 == 1:
            # Toggle triple string mode after emitting the line.
            if not in_triple:
                # Starting triple: keep the line exactly (no indent normalization).
                out.append(raw.rstrip())
                in_triple = True
                continue
            # Ending triple: keep line exactly and exit mode.
            out.append(raw.rstrip())
            in_triple = False
            continue

        if in_triple:
            out.append(raw.rstrip())
            continue

        stripped = raw.strip()

        # Comments keep indentation but normalize whitespace.
        if stripped.startswith("#"):
            out.append((" " * (indent * 4)) + stripped)
            continue

        # Dedent for end/else
        if stripped.startswith("end"):
            indent = max(indent - 1, 0)
        elif stripped.startswith("else"):
            indent = max(indent - 1, 0)

        out.append((" " * (indent * 4)) + stripped)

        # Indent after block openers
        if stripped.endswith("do") and (
            stripped.startswith("when ")
            or stripped.startswith("else ")
            or stripped.startswith("repeat ")
            or stripped.startswith("count ")
            or stripped.startswith("each ")
            or stripped.startswith("work ")
        ):
            indent += 1

    formatted = "\n".join(out) + ("\n" if source.endswith("\n") else "")
    return FormatResult(formatted=formatted, changed=(formatted != source))

