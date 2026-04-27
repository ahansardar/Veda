from __future__ import annotations

import pytest

from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser
from veda.errors import VedaNameError


def test_name_error_includes_code_and_suggestion() -> None:
    source = 'make name = "Ahan"\nshow nmae\n'
    tokens = Lexer(source, filename="test.veda").tokenize()
    program = Parser(tokens, source=source, filename="test.veda").parse()
    interpreter = Interpreter(source=source, filename="test.veda", output=lambda s: None)

    with pytest.raises(VedaNameError) as e:
        interpreter.run(program)

    pretty = e.value.pretty()
    assert "[V101]" in pretty
    assert "Did you mean 'name'" in pretty

