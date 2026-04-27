from __future__ import annotations

import pytest

from veda.errors import VedaNameError
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser


def run(source: str) -> list[str]:
    out: list[str] = []
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    interpreter = Interpreter(source=source, filename="test.veda", output=out.append, input_fn=lambda p: "x")
    interpreter.run(program)
    return out


def test_interpreting_show_statement() -> None:
    assert run('show "hello"\n') == ["hello"]


def test_interpreting_variables() -> None:
    out = run('make x = 10\nshow x\nshow x + 5\n')
    assert out == ["10", "15"]


def test_interpreting_functions() -> None:
    out = run(
        "work add(a, b) do\n"
        "    give a + b\n"
        "end\n"
        "show add(10, 20)\n"
    )
    assert out == ["30"]


def test_builtins_text_and_math_helpers() -> None:
    out = run('show upper("hi")\nshow lower("HI")\nshow trim("  ok  ")\nshow abs(-5)\n')
    assert out == ["HI", "hi", "ok", "5"]


def test_runtime_error_for_undefined_variable() -> None:
    source = "show missing\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    interpreter = Interpreter(source=source, filename="test.veda", output=lambda s: None)
    with pytest.raises(VedaNameError):
        interpreter.run(program)
