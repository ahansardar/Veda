from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpan:
    filename: str
    line: int
    column: int
    length: int = 1


@dataclass(frozen=True)
class TraceFrame:
    name: str
    span: SourceSpan


def format_error(name: str, message: str, source: str, span: SourceSpan) -> str:
    lines = source.splitlines()
    line_index = max(span.line - 1, 0)
    code_line = lines[line_index] if line_index < len(lines) else ""
    if code_line.startswith("\ufeff"):
        code_line = code_line[1:]

    caret_col = max(span.column, 1)
    underline = "^" * max(span.length, 1)
    pointer = " " * (caret_col - 1) + underline

    gutter = f"{span.line} | "
    return (
        f"{name} in {span.filename} at line {span.line}, column {span.column}:\n"
        f"{message}\n\n"
        f"{gutter}{code_line}\n"
        f"{' ' * len(gutter)}{pointer}"
    )


class VedaError(Exception):
    default_code = "V000"

    def __init__(
        self,
        message: str,
        *,
        source: str,
        span: SourceSpan,
        trace: list[TraceFrame] | None = None,
        code: str | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.source = source
        self.span = span
        self.trace = trace or []
        self.code = code or self.default_code

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def pretty(self) -> str:
        head = ""
        if self.trace:
            lines = ["Veda stack trace (most recent call last):"]
            for frame in self.trace:
                lines.append(
                    f"  in {frame.name} ({frame.span.filename}:{frame.span.line}:{frame.span.column})"
                )
            head = "\n".join(lines) + "\n\n"
        return head + format_error(f"{self.name} [{self.code}]", self.message, self.source, self.span)


class VedaSyntaxError(VedaError):
    default_code = "V001"
    pass


class VedaRuntimeError(VedaError):
    default_code = "V300"
    pass


class VedaNameError(VedaRuntimeError):
    default_code = "V101"
    pass


class VedaTypeError(VedaRuntimeError):
    default_code = "V201"
    pass


class VedaCheckError(VedaError):
    default_code = "V401"
    pass
