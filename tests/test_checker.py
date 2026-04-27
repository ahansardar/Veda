from __future__ import annotations

from veda.checker import Checker
from veda.builtins import BuiltinFunction
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser


def test_checker_reports_undefined_variable() -> None:
    source = "show x\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    tmp = Interpreter(source=source, filename="test.veda", output=lambda s: None)
    builtins = tmp.builtin_names | {"args"}
    arity = {
        n: (v.min_arity, v.max_arity) for n, v in tmp.globals.values.items() if isinstance(v, BuiltinFunction)
    }
    errors = Checker(filename="test.veda", source=source, builtin_names=builtins, builtin_arity=arity).check(program)
    assert len(errors) == 1
    assert "Undefined variable 'x'" in errors[0].message


def test_checker_reports_builtin_arity() -> None:
    source = 'show len("a", "b")\n'
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    tmp = Interpreter(source=source, filename="test.veda", output=lambda s: None)
    builtins = tmp.builtin_names | {"args"}
    arity = {
        n: (v.min_arity, v.max_arity) for n, v in tmp.globals.values.items() if isinstance(v, BuiltinFunction)
    }
    errors = Checker(filename="test.veda", source=source, builtin_names=builtins, builtin_arity=arity).check(program)
    assert len(errors) == 1
    assert "len() expects" in errors[0].message
