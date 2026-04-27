from __future__ import annotations

from veda.checker import Checker
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser


def test_checker_reports_undefined_variable() -> None:
    source = "show x\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    builtins = Interpreter(source=source, filename="test.veda", output=lambda s: None).builtin_names | {"args"}
    errors = Checker(filename="test.veda", source=source, builtin_names=builtins).check(program)
    assert len(errors) == 1
    assert "Undefined variable 'x'" in errors[0].message

