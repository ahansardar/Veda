from __future__ import annotations

from veda.lexer import Lexer
from veda.token_types import TokenType


def test_tokenizing_keywords() -> None:
    source = "make x = 1\nshow x\nwhen true do\nend\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    kinds = [(t.type, t.lexeme) for t in tokens if t.type != TokenType.NEWLINE]
    assert (TokenType.KEYWORD, "make") in kinds
    assert (TokenType.KEYWORD, "show") in kinds
    assert (TokenType.KEYWORD, "when") in kinds
    assert (TokenType.KEYWORD, "true") in kinds
    assert (TokenType.KEYWORD, "do") in kinds
    assert (TokenType.KEYWORD, "end") in kinds


def test_tokenizing_strings_and_numbers() -> None:
    source = 'make a = "hi"\nmake b = 12\nmake c = 3.14\n'
    tokens = Lexer(source, filename="test.veda").tokenize()
    string_tokens = [t for t in tokens if t.type == TokenType.STRING]
    number_tokens = [t for t in tokens if t.type == TokenType.NUMBER]
    assert string_tokens[0].literal == "hi"
    assert number_tokens[0].literal == 12
    assert number_tokens[1].literal == 3.14


def test_tokenizing_list_brackets() -> None:
    source = "show [1, 2]\n"
    tokens = Lexer(source, filename="test.veda").tokenize()
    kinds = [t.type for t in tokens]
    assert TokenType.LBRACKET in kinds
    assert TokenType.RBRACKET in kinds
