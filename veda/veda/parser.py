from __future__ import annotations

from typing import List, Optional

from veda.ast_nodes import (
    AskStatement,
    Assignment,
    BinaryExpression,
    CountStatement,
    ExpressionStatement,
    FunctionCall,
    GiveStatement,
    Identifier,
    Literal,
    Program,
    RepeatStatement,
    ShowStatement,
    UnaryExpression,
    VariableDeclaration,
    WhenStatement,
    WorkDeclaration,
)
from veda.errors import SourceSpan, VedaSyntaxError
from veda.token_types import Token, TokenType


class Parser:
    def __init__(self, tokens: list[Token], *, source: str, filename: str):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.current = 0

    def parse(self) -> Program:
        statements: list = []
        self._skip_newlines()
        while not self._is_at_end():
            statements.append(self._statement())
            self._skip_newlines()
        return Program(statements=statements)

    # --- Helpers ---
    def _peek(self) -> Token:
        return self.tokens[self.current]

    def _peek_next(self) -> Token:
        idx = self.current + 1
        return self.tokens[idx] if idx < len(self.tokens) else self.tokens[-1]

    def _previous(self) -> Token:
        return self.tokens[self.current - 1]

    def _is_at_end(self) -> bool:
        return self._peek().type == TokenType.EOF

    def _advance(self) -> Token:
        if not self._is_at_end():
            self.current += 1
        return self._previous()

    def _check(self, t: TokenType) -> bool:
        if self._is_at_end():
            return False
        return self._peek().type == t

    def _match(self, *types: TokenType) -> bool:
        for t in types:
            if self._check(t):
                self._advance()
                return True
        return False

    def _check_keyword(self, value: str) -> bool:
        tok = self._peek()
        return tok.type == TokenType.KEYWORD and tok.lexeme == value

    def _match_keyword(self, value: str) -> bool:
        if self._check_keyword(value):
            self._advance()
            return True
        return False

    def _expect(self, token_type: TokenType, message: str) -> Token:
        if self._check(token_type):
            return self._advance()
        raise self._error(self._peek(), message)

    def _expect_keyword(self, value: str, message: str) -> Token:
        if self._check_keyword(value):
            return self._advance()
        raise self._error(self._peek(), message)

    def _skip_newlines(self) -> None:
        while self._match(TokenType.NEWLINE):
            pass

    def _error(self, token: Token, message: str) -> VedaSyntaxError:
        span = SourceSpan(
            filename=token.filename,
            line=token.line,
            column=token.column,
            length=max(token.length, 1),
        )
        return VedaSyntaxError(message, source=self.source, span=span)

    def _consume_line_end(self) -> None:
        if self._match(TokenType.NEWLINE):
            self._skip_newlines()
            return
        if self._is_at_end() or self._check_keyword("end") or self._check_keyword("else"):
            return
        raise self._error(self._peek(), "Expected end of line after statement.")

    # --- Statements ---
    def _statement(self):
        if self._match_keyword("make"):
            stmt = self._variable_decl()
            self._consume_line_end()
            return stmt

        if self._match_keyword("show"):
            expr = self._expression()
            self._consume_line_end()
            return ShowStatement(expression=expr)

        if self._match_keyword("ask"):
            name = self._expect(TokenType.IDENTIFIER, "Expected variable name after 'ask'.")
            self._expect(TokenType.EQUAL, "Expected '=' after variable name.")
            prompt = self._expression()
            self._consume_line_end()
            return AskStatement(name=name, prompt=prompt)

        if self._match_keyword("when"):
            return self._when_stmt()

        if self._match_keyword("repeat"):
            return self._repeat_stmt()

        if self._match_keyword("count"):
            return self._count_stmt()

        if self._match_keyword("work"):
            return self._work_decl()

        if self._match_keyword("give"):
            value = self._expression()
            self._consume_line_end()
            return GiveStatement(value=value)

        if self._check(TokenType.IDENTIFIER) and self._peek_next().type == TokenType.EQUAL:
            name = self._advance()
            self._advance()  # '='
            value = self._expression()
            self._consume_line_end()
            return Assignment(name=name, value=value)

        expr = self._expression()
        self._consume_line_end()
        return ExpressionStatement(expression=expr)

    def _variable_decl(self) -> VariableDeclaration:
        name = self._expect(TokenType.IDENTIFIER, "Expected variable name after 'make'.")
        self._expect(TokenType.EQUAL, "Expected '=' after variable name.")
        initializer = self._expression()
        return VariableDeclaration(name=name, initializer=initializer)

    def _when_stmt(self) -> WhenStatement:
        condition = self._expression()
        self._expect_keyword("do", "Expected 'do' after condition.")
        self._skip_newlines()

        then_branch = self._block(terminators={"else", "end"})
        else_branch: Optional[List] = None

        if self._match_keyword("else"):
            self._expect_keyword("do", "Expected 'do' after 'else'.")
            self._skip_newlines()
            else_branch = self._block(terminators={"end"})

        self._expect_keyword("end", "Expected 'end' to close 'when' block.")
        self._consume_line_end()
        return WhenStatement(condition=condition, then_branch=then_branch, else_branch=else_branch)

    def _repeat_stmt(self) -> RepeatStatement:
        times = self._expression()
        self._expect_keyword("times", "Expected 'times' after repeat count.")
        self._expect_keyword("do", "Expected 'do' after 'times'.")
        self._skip_newlines()
        body = self._block(terminators={"end"})
        self._expect_keyword("end", "Expected 'end' to close repeat block.")
        self._consume_line_end()
        return RepeatStatement(times=times, body=body)

    def _count_stmt(self) -> CountStatement:
        name = self._expect(TokenType.IDENTIFIER, "Expected loop variable name after 'count'.")
        self._expect_keyword("from", "Expected 'from' after loop variable.")
        start = self._expression()
        self._expect_keyword("to", "Expected 'to' after start value.")
        end = self._expression()
        self._expect_keyword("do", "Expected 'do' after range.")
        self._skip_newlines()
        body = self._block(terminators={"end"})
        self._expect_keyword("end", "Expected 'end' to close count block.")
        self._consume_line_end()
        return CountStatement(name=name, start=start, end=end, body=body)

    def _work_decl(self) -> WorkDeclaration:
        name = self._expect(TokenType.IDENTIFIER, "Expected function name after 'work'.")
        self._expect(TokenType.LPAREN, "Expected '(' after function name.")
        params: list[Token] = []
        if not self._check(TokenType.RPAREN):
            params.append(self._expect(TokenType.IDENTIFIER, "Expected parameter name."))
            while self._match(TokenType.COMMA):
                params.append(self._expect(TokenType.IDENTIFIER, "Expected parameter name."))
        self._expect(TokenType.RPAREN, "Expected ')' after parameters.")
        self._expect_keyword("do", "Expected 'do' after function signature.")
        self._skip_newlines()
        body = self._block(terminators={"end"})
        self._expect_keyword("end", "Expected 'end' to close function.")
        self._consume_line_end()
        return WorkDeclaration(name=name, params=params, body=body)

    def _block(self, *, terminators: set[str]) -> List:
        statements: list = []
        self._skip_newlines()
        while not self._is_at_end() and not (
            self._peek().type == TokenType.KEYWORD and self._peek().lexeme in terminators
        ):
            statements.append(self._statement())
            self._skip_newlines()
        return statements

    # --- Expressions ---
    def _expression(self):
        return self._logic_or()

    def _logic_or(self):
        expr = self._logic_and()
        while self._match_keyword("or"):
            op = self._previous()
            right = self._logic_and()
            expr = BinaryExpression(left=expr, operator=op, right=right)
        return expr

    def _logic_and(self):
        expr = self._equality()
        while self._match_keyword("and"):
            op = self._previous()
            right = self._equality()
            expr = BinaryExpression(left=expr, operator=op, right=right)
        return expr

    def _equality(self):
        expr = self._comparison()
        while self._match(TokenType.EQUAL_EQUAL, TokenType.BANG_EQUAL):
            op = self._previous()
            right = self._comparison()
            expr = BinaryExpression(left=expr, operator=op, right=right)
        return expr

    def _comparison(self):
        expr = self._term()
        while self._match(
            TokenType.GREATER,
            TokenType.GREATER_EQUAL,
            TokenType.LESS,
            TokenType.LESS_EQUAL,
        ):
            op = self._previous()
            right = self._term()
            expr = BinaryExpression(left=expr, operator=op, right=right)
        return expr

    def _term(self):
        expr = self._factor()
        while self._match(TokenType.PLUS, TokenType.MINUS):
            op = self._previous()
            right = self._factor()
            expr = BinaryExpression(left=expr, operator=op, right=right)
        return expr

    def _factor(self):
        expr = self._unary()
        while self._match(TokenType.STAR, TokenType.SLASH, TokenType.PERCENT):
            op = self._previous()
            right = self._unary()
            expr = BinaryExpression(left=expr, operator=op, right=right)
        return expr

    def _unary(self):
        if self._match_keyword("not") or self._match(TokenType.MINUS):
            op = self._previous()
            right = self._unary()
            return UnaryExpression(operator=op, right=right)
        return self._call()

    def _call(self):
        expr = self._primary()
        while self._match(TokenType.LPAREN):
            paren = self._previous()
            args: list = []
            if not self._check(TokenType.RPAREN):
                args.append(self._expression())
                while self._match(TokenType.COMMA):
                    args.append(self._expression())
            self._expect(TokenType.RPAREN, "Expected ')' after arguments.")
            expr = FunctionCall(callee=expr, paren=paren, arguments=args)
        return expr

    def _primary(self):
        if self._match(TokenType.NUMBER):
            tok = self._previous()
            return Literal(value=tok.literal, token=tok)

        if self._match(TokenType.STRING):
            tok = self._previous()
            return Literal(value=tok.literal, token=tok)

        if self._match_keyword("true"):
            tok = self._previous()
            return Literal(value=True, token=tok)

        if self._match_keyword("false"):
            tok = self._previous()
            return Literal(value=False, token=tok)

        if self._match(TokenType.IDENTIFIER):
            return Identifier(name=self._previous())

        if self._match(TokenType.LPAREN):
            expr = self._expression()
            self._expect(TokenType.RPAREN, "Expected ')' after expression.")
            return expr

        raise self._error(self._peek(), "Expected expression.")

