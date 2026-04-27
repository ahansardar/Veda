from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class TokenType(Enum):
    EOF = auto()
    NEWLINE = auto()

    IDENTIFIER = auto()
    KEYWORD = auto()
    NUMBER = auto()
    STRING = auto()

    LPAREN = auto()
    RPAREN = auto()
    COMMA = auto()
    LBRACKET = auto()
    RBRACKET = auto()

    PLUS = auto()
    MINUS = auto()
    STAR = auto()
    SLASH = auto()
    PERCENT = auto()

    EQUAL = auto()
    EQUAL_EQUAL = auto()
    BANG_EQUAL = auto()

    GREATER = auto()
    GREATER_EQUAL = auto()
    LESS = auto()
    LESS_EQUAL = auto()


KEYWORDS = {
    "make",
    "show",
    "ask",
    "when",
    "else",
    "repeat",
    "times",
    "count",
    "from",
    "to",
    "work",
    "give",
    "end",
    "do",
    "true",
    "false",
    "and",
    "or",
    "not",
}


@dataclass(frozen=True)
class Token:
    type: TokenType
    lexeme: str
    literal: Any
    filename: str
    line: int
    column: int
    length: int

    def is_keyword(self, value: str) -> bool:
        return self.type == TokenType.KEYWORD and self.lexeme == value
