from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SourceSpan:
    filename: str
    line: int
    column: int
    length: int = 1


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
    def __init__(self, message: str, *, source: str, span: SourceSpan):
        super().__init__(message)
        self.message = message
        self.source = source
        self.span = span

    @property
    def name(self) -> str:
        return self.__class__.__name__

    def pretty(self) -> str:
        return format_error(self.name, self.message, self.source, self.span)


class VedaSyntaxError(VedaError):
    pass


class VedaRuntimeError(VedaError):
    pass


class VedaNameError(VedaRuntimeError):
    pass


class VedaTypeError(VedaRuntimeError):
    pass


class VedaCheckError(VedaError):
    pass
