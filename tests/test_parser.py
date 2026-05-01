from __future__ import annotations

from veda.ast_nodes import BinaryExpression, DictLiteral, IndexExpression, ListLiteral, Literal, Program, SliceExpression, VariableDeclaration, WhenStatement
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
    # Constant folding may reduce this expression to a literal.
    if isinstance(expr, Literal):
        assert expr.value == 7
    else:
        assert isinstance(expr, BinaryExpression)
        assert expr.operator.lexeme == "+"


def test_parse_with_errors_collects_multiple_errors() -> None:
    source = "make x =\nshow 1 +\nshow \"ok\"\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    program, errors = Parser(tokens, source=source, filename="test.veda").parse_with_errors()
    assert len(errors) == 2
    assert len(program.statements) == 1


def test_parsing_list_literal_and_index() -> None:
    source = "make a = [1, 2, 3]\nshow a[0]\n"
    program = parse(source)
    decl = program.statements[0]
    assert isinstance(decl, VariableDeclaration)
    assert isinstance(decl.initializer, ListLiteral)
    show_stmt = program.statements[1]
    expr = show_stmt.expression  # type: ignore[attr-defined]
    assert isinstance(expr, IndexExpression)


def test_parsing_slice_and_map_literal() -> None:
    source = 'make m = {"a": 1}\nshow [1, 2, 3][1:]\n'
    program = parse(source)
    decl = program.statements[0]
    assert isinstance(decl, VariableDeclaration)
    assert isinstance(decl.initializer, DictLiteral)
    show_stmt = program.statements[1]
    expr = show_stmt.expression  # type: ignore[attr-defined]
    assert isinstance(expr, SliceExpression)


def test_when_supports_else_when_chain() -> None:
    source = (
        'make op = "-"\n'
        'make a = 10\n'
        'make b = 3\n'
        "when op == \"+\" do\n"
        "    show a + b\n"
        "else when op == \"-\" do\n"
        "    show a - b\n"
        "else do\n"
        "    show 0\n"
        "end\n"
    )
    program = parse(source)
    stmt = program.statements[3]
    assert isinstance(stmt, WhenStatement)
    assert stmt.else_branch is not None
    assert len(stmt.else_branch) == 1
    assert isinstance(stmt.else_branch[0], WhenStatement)
