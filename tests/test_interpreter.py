from __future__ import annotations

import pytest

from veda.errors import VedaNameError, VedaRuntimeError
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
    out = run(
        'show upper("hi")\n'
        'show lower("HI")\n'
        'show trim("  ok  ")\n'
        'show replace("a-b-c", "-", "_")\n'
        'show contains("hello", "ell")\n'
        'show starts("hello", "he")\n'
        'show ends("hello", "lo")\n'
        'show find("hello", "z")\n'
        'show slice("hello", 1, 4)\n'
        'show repeat_text("ha", 3)\n'
        "show abs(-5)\n"
        "show floor(2.9)\n"
        "show ceil(2.1)\n"
        "show round(2.5)\n"
        "show sqrt(9)\n"
        "show pow(2, 3)\n"
        "show min(2, 3)\n"
        "show max(2, 3)\n"
        "show clamp(10, 0, 5)\n"
        "show pi\n"
    )
    assert out == [
        "HI",
        "hi",
        "ok",
        "a_b_c",
        "true",
        "true",
        "true",
        "-1",
        "ell",
        "hahaha",
        "5",
        "2",
        "3",
        "3",
        "3.0",
        "8",
        "2",
        "3",
        "5",
        str(__import__("math").pi),
    ]


def test_runtime_error_for_undefined_variable() -> None:
    source = "show missing\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    interpreter = Interpreter(source=source, filename="test.veda", output=lambda s: None)
    with pytest.raises(VedaNameError):
        interpreter.run(program)


def test_lists_and_indexing() -> None:
    out = run("make a = [1, 2, 3]\nshow a\nshow a[1]\n")
    assert out == ["[1, 2, 3]", "2"]

def test_slicing_and_maps() -> None:
    out = run('make t = "hello"\nshow t[1:4]\nmake m = {"a": 10}\nshow m["a"]\n')
    assert out == ["ell", "10"]


def test_index_assignment() -> None:
    out = run("make a = [1, 2, 3]\na[0] = 9\nshow a\nmake m = {\"k\": 1}\nm[\"k\"] = 7\nshow m[\"k\"]\n")
    assert out == ["[9, 2, 3]", "7"]


def test_each_loop_over_list_and_text() -> None:
    out = run('make s = ""\nmake items = ["a", "b"]\neach x in items do\n    s = s + x\nend\nshow s\neach c in "hi" do\n    show c\nend\n')
    assert out == ["ab", "h", "i"]


def test_text_interpolation() -> None:
    out = run('make name = "Ahan"\nshow "Hello {name}"\nshow "{{ok}}"\n')
    assert out == ["Hello Ahan", "{ok}"]


def test_use_runs_once_with_cache(tmp_path) -> None:
    lib = tmp_path / "lib.veda"
    lib.write_text("make x = 0\nx = x + 1\n", encoding="utf-8")
    main = tmp_path / "main.veda"
    main.write_text(f'use "{lib.as_posix()}"\nuse "{lib.as_posix()}"\nshow x\n', encoding="utf-8")

    source = main.read_text(encoding="utf-8")
    out: list[str] = []
    tokens = Lexer(source, filename=str(main)).tokenize()
    program = Parser(tokens, source=source, filename=str(main)).parse()
    interpreter = Interpreter(source=source, filename=str(main), output=out.append)
    interpreter.run(program)
    assert out == ["1"]


def test_give_outside_function_is_runtime_error() -> None:
    source = "give 1\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    interpreter = Interpreter(source=source, filename="test.veda", output=lambda s: None)
    with pytest.raises(VedaRuntimeError) as e:
        interpreter.run(program)
    assert "give can only be used" in str(e.value)
