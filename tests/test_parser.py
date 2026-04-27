from __future__ import annotations

from veda.ast_nodes import BinaryExpression, Program, VariableDeclaration
from veda.lexer import Lexer
from veda.parser import Parser


def parse(source: str) -> Program:
    tokens = Lexer(source, filename="test.veda").tokenize()
    return Parser(tokens, source=source, filename="test.veda").parse()


def test_parsing_variable_declaration() -> None:
    program = parse('make x = "hello"\n')
    assert len(program.statements) == 1
    stmt = program.statements[0]
    assert isinstance(stmt, VariableDeclaration)
    assert stmt.name.lexeme == "x"


def test_parsing_arithmetic_expression() -> None:
    program = parse("show 1 + 2 * 3\n")
    show_stmt = program.statements[0]
    expr = show_stmt.expression  # type: ignore[attr-defined]
    assert isinstance(expr, BinaryExpression)
    assert expr.operator.lexeme == "+"


def test_parse_with_errors_collects_multiple_errors() -> None:
    source = "make x =\nshow 1 +\nshow \"ok\"\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program, errors = Parser(tokens, source=source, filename="test.veda").parse_with_errors()
    assert len(errors) == 2
    assert len(program.statements) == 1
