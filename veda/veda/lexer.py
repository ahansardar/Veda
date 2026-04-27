from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List

from veda.errors import SourceSpan, VedaSyntaxError
from veda.token_types import KEYWORDS, Token, TokenType


@dataclass
class _Cursor:
    index: int = 0
    line: int = 1
    column: int = 1


class Lexer:
    def __init__(self, source: str, *, filename: str = "<stdin>"):
        self.source = source
        self.filename = filename
        self._cursor = _Cursor()
        self._tokens: List[Token] = []

    def tokenize(self) -> list[Token]:
        tokens, errors = self.tokenize_with_errors()
        if errors:
            raise errors[0]
        return tokens

    def tokenize_with_errors(self) -> tuple[list[Token], list[VedaSyntaxError]]:
        # Allow reusing a Lexer instance in tooling.
        self._cursor = _Cursor()
        self._tokens = []
        errors: list[VedaSyntaxError] = []
        while not self._is_at_end():
            try:
                ch = self._peek()

                # Some editors on Windows may save UTF-8 with a BOM.
                # Treat it as invisible whitespace so beginners don't get a confusing error.
                if ch == "\ufeff":
                    if self._cursor.index == 0 and self._cursor.line == 1 and self._cursor.column == 1:
                        self._cursor.index += 1
                    else:
                        self._advance()
                    continue

                if ch in " \t\r":
                    self._advance()
                    continue

                if ch == "\n":
                    self._add_token(TokenType.NEWLINE, "\n", None, length=1)
                    self._advance_line()
                    continue

                if ch == "#":
                    self._skip_comment()
                    continue

                if ch == '"':
                    self._lex_string()
                    continue

                if ch.isdigit():
                    self._lex_number()
                    continue

                if ch.isalpha() or ch == "_":
                    self._lex_identifier_or_keyword()
                    continue

                self._lex_symbol()
            except VedaSyntaxError as e:
                errors.append(e)
                self._recover_from_error()

        self._tokens.append(
            Token(
                type=TokenType.EOF,
                lexeme="",
                literal=None,
                filename=self.filename,
                line=self._cursor.line,
                column=self._cursor.column,
                length=0,
            )
        )
        return self._tokens, errors

    def _is_at_end(self) -> bool:
        return self._cursor.index >= len(self.source)

    def _peek(self) -> str:
        return self.source[self._cursor.index]

    def _peek_next(self) -> str:
        nxt = self._cursor.index + 1
        return self.source[nxt] if nxt < len(self.source) else "\0"

    def _advance(self) -> str:
        ch = self.source[self._cursor.index]
        self._cursor.index += 1
        self._cursor.column += 1
        return ch

    def _advance_line(self) -> None:
        self._cursor.index += 1
        self._cursor.line += 1
        self._cursor.column = 1

    def _add_token(self, token_type: TokenType, lexeme: str, literal: Any, *, length: int) -> None:
        self._tokens.append(
            Token(
                type=token_type,
                lexeme=lexeme,
                literal=literal,
                filename=self.filename,
                line=self._cursor.line,
                column=self._cursor.column,
                length=length,
            )
        )

    def _error(self, message: str, *, length: int = 1) -> VedaSyntaxError:
        return VedaSyntaxError(
            message,
            source=self.source,
            span=SourceSpan(
                filename=self.filename,
                line=self._cursor.line,
                column=self._cursor.column,
                length=length,
            ),
        )

    def _skip_comment(self) -> None:
        while not self._is_at_end() and self._peek() != "\n":
            self._advance()

    def _lex_string(self) -> None:
        start_line = self._cursor.line
        start_col = self._cursor.column
        start_index = self._cursor.index
        self._advance()  # opening quote

        chars: list[str] = []
        while not self._is_at_end():
            ch = self._peek()
            if ch == '"':
                self._advance()
                lexeme = self.source[start_index : self._cursor.index]
                value = self._unescape("".join(chars))
                length = self._cursor.column - start_col
                self._tokens.append(
                    Token(
                        type=TokenType.STRING,
                        lexeme=lexeme,
                        literal=value,
                        filename=self.filename,
                        line=start_line,
                        column=start_col,
                        length=length,
                    )
                )
                return

            if ch == "\n":
                raise VedaSyntaxError(
                    "Unterminated string literal.",
                    source=self.source,
                    span=SourceSpan(
                        filename=self.filename,
                        line=start_line,
                        column=start_col,
                        length=1,
                    ),
                )

            chars.append(self._advance())

        raise VedaSyntaxError(
            "Unterminated string literal.",
            source=self.source,
            span=SourceSpan(
                filename=self.filename,
                line=start_line,
                column=start_col,
                length=1,
            ),
        )

    def _recover_from_error(self) -> None:
        """
        Best-effort recovery for `tokenize_with_errors()`.
        Advance at least one character, and for broken strings skip to end of line.
        """
        if self._is_at_end():
            return
        ch = self._peek()
        if ch == '"':
            # Skip until newline or closing quote (prefer newline to keep line accounting stable).
            self._advance()  # skip opening quote
            while not self._is_at_end() and self._peek() not in {'"', "\n"}:
                self._advance()
            if not self._is_at_end() and self._peek() == '"':
                self._advance()
            return

        if ch == "\n":
            self._advance_line()
            return

        self._advance()

    def _unescape(self, value: str) -> str:
        out: list[str] = []
        i = 0
        while i < len(value):
            ch = value[i]
            if ch != "\\":
                out.append(ch)
                i += 1
                continue

            if i + 1 >= len(value):
                out.append("\\")
                break

            nxt = value[i + 1]
            if nxt == "n":
                out.append("\n")
            elif nxt == "t":
                out.append("\t")
            elif nxt == '"':
                out.append('"')
            elif nxt == "\\":
                out.append("\\")
            else:
                out.append(nxt)
            i += 2
        return "".join(out)

    def _lex_number(self) -> None:
        start_index = self._cursor.index
        start_line = self._cursor.line
        start_col = self._cursor.column

        while not self._is_at_end() and self._peek().isdigit():
            self._advance()

        is_float = False
        if not self._is_at_end() and self._peek() == "." and self._peek_next().isdigit():
            is_float = True
            self._advance()  # '.'
            while not self._is_at_end() and self._peek().isdigit():
                self._advance()

        text = self.source[start_index : self._cursor.index]
        literal: Any = float(text) if is_float else int(text)
        length = self._cursor.column - start_col
        self._tokens.append(
            Token(
                type=TokenType.NUMBER,
                lexeme=text,
                literal=literal,
                filename=self.filename,
                line=start_line,
                column=start_col,
                length=length,
            )
        )

    def _lex_identifier_or_keyword(self) -> None:
        start_index = self._cursor.index
        start_line = self._cursor.line
        start_col = self._cursor.column

        while not self._is_at_end():
            ch = self._peek()
            if ch.isalnum() or ch == "_":
                self._advance()
            else:
                break

        text = self.source[start_index : self._cursor.index]
        token_type = TokenType.KEYWORD if text in KEYWORDS else TokenType.IDENTIFIER
        length = self._cursor.column - start_col
        self._tokens.append(
            Token(
                type=token_type,
                lexeme=text,
                literal=None,
                filename=self.filename,
                line=start_line,
                column=start_col,
                length=length,
            )
        )

    def _lex_symbol(self) -> None:
        ch = self._peek()

        def two(a: str, b: str) -> bool:
            return ch == a and self._peek_next() == b

        if two("=", "="):
            self._add_token(TokenType.EQUAL_EQUAL, "==", None, length=2)
            self._advance()
            self._advance()
            return

        if two("!", "="):
            self._add_token(TokenType.BANG_EQUAL, "!=", None, length=2)
            self._advance()
            self._advance()
            return

        if two(">", "="):
            self._add_token(TokenType.GREATER_EQUAL, ">=", None, length=2)
            self._advance()
            self._advance()
            return

        if two("<", "="):
            self._add_token(TokenType.LESS_EQUAL, "<=", None, length=2)
            self._advance()
            self._advance()
            return

        single_map = {
            "(": TokenType.LPAREN,
            ")": TokenType.RPAREN,
            ",": TokenType.COMMA,
            "+": TokenType.PLUS,
            "-": TokenType.MINUS,
            "*": TokenType.STAR,
            "/": TokenType.SLASH,
            "%": TokenType.PERCENT,
            "=": TokenType.EQUAL,
            ">": TokenType.GREATER,
            "<": TokenType.LESS,
        }

        if ch in single_map:
            token_type = single_map[ch]
            self._add_token(token_type, ch, None, length=1)
            self._advance()
            return

        raise self._error(f"Unexpected character '{ch}'.", length=1)
