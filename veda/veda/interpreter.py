from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Callable, Optional

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
from veda.builtins import BuiltinFunction, to_veda_text, veda_type_name
from veda.environment import Environment
from veda.errors import SourceSpan, VedaNameError, VedaRuntimeError, VedaTypeError
from veda.token_types import Token, TokenType


class _ReturnSignal(Exception):
    def __init__(self, value: Any):
        self.value = value


@dataclass(frozen=True)
class VedaFunction:
    name: str
    params: list[str]
    body: list
    closure: Environment

    def __repr__(self) -> str:
        return f"<work {self.name}>"


class Interpreter:
    def __init__(
        self,
        *,
        source: str,
        filename: str,
        output: Optional[Callable[[str], None]] = None,
        input_fn: Optional[Callable[[str], str]] = None,
    ):
        self.source = source
        self.filename = filename
        self.output = output or (lambda s: print(s))
        self.input_fn = input_fn or (lambda prompt: input(prompt))

        self.globals = Environment(values={})
        self.env = self.globals
        self._install_builtins()

    def _install_builtins(self) -> None:
        def _len(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if not isinstance(value, str):
                raise VedaTypeError("len() expects a text value.", source=source, span=span)
            return len(value)

        def _type(args: list[Any], source: str, span: SourceSpan) -> Any:
            return veda_type_name(args[0])

        def _text(args: list[Any], source: str, span: SourceSpan) -> Any:
            return to_veda_text(args[0])

        def _num(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool):
                raise VedaTypeError("num() cannot convert bool.", source=source, span=span)
            if isinstance(value, (int, float)):
                return value
            if isinstance(value, str):
                s = value.strip()
                if s == "":
                    raise VedaTypeError("num() cannot convert empty text.", source=source, span=span)
                try:
                    if "." in s:
                        return float(s)
                    return int(s)
                except ValueError as e:
                    raise VedaTypeError("num() could not convert text to number.", source=source, span=span) from e
            raise VedaTypeError("num() expects a number or text.", source=source, span=span)

        def _upper(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if not isinstance(value, str):
                raise VedaTypeError("upper() expects a text value.", source=source, span=span)
            return value.upper()

        def _lower(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if not isinstance(value, str):
                raise VedaTypeError("lower() expects a text value.", source=source, span=span)
            return value.lower()

        def _trim(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if not isinstance(value, str):
                raise VedaTypeError("trim() expects a text value.", source=source, span=span)
            return value.strip()

        def _abs(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("abs() expects a number value.", source=source, span=span)
            return abs(value)

        def _floor(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("floor() expects a number value.", source=source, span=span)
            return math.floor(value)

        def _ceil(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("ceil() expects a number value.", source=source, span=span)
            return math.ceil(value)

        def _round(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("round() expects a number value.", source=source, span=span)
            return round(value)

        self.globals.define("len", BuiltinFunction("len", _len, min_arity=1, max_arity=1))
        self.globals.define("type", BuiltinFunction("type", _type, min_arity=1, max_arity=1))
        self.globals.define("text", BuiltinFunction("text", _text, min_arity=1, max_arity=1))
        self.globals.define("num", BuiltinFunction("num", _num, min_arity=1, max_arity=1))
        self.globals.define("upper", BuiltinFunction("upper", _upper, min_arity=1, max_arity=1))
        self.globals.define("lower", BuiltinFunction("lower", _lower, min_arity=1, max_arity=1))
        self.globals.define("trim", BuiltinFunction("trim", _trim, min_arity=1, max_arity=1))
        self.globals.define("abs", BuiltinFunction("abs", _abs, min_arity=1, max_arity=1))
        self.globals.define("floor", BuiltinFunction("floor", _floor, min_arity=1, max_arity=1))
        self.globals.define("ceil", BuiltinFunction("ceil", _ceil, min_arity=1, max_arity=1))
        self.globals.define("round", BuiltinFunction("round", _round, min_arity=1, max_arity=1))

    def run(self, program: Program) -> None:
        for stmt in program.statements:
            self._execute(stmt)

    # --- Statements ---
    def _execute(self, stmt) -> None:
        if isinstance(stmt, VariableDeclaration):
            value = self._evaluate(stmt.initializer)
            self.env.define(stmt.name.lexeme, value)
            return

        if isinstance(stmt, Assignment):
            value = self._evaluate(stmt.value)
            self.env.assign(stmt.name.lexeme, value, source=self.source, span=self._span(stmt.name))
            return

        if isinstance(stmt, ShowStatement):
            value = self._evaluate(stmt.expression)
            self.output(to_veda_text(value))
            return

        if isinstance(stmt, AskStatement):
            prompt_value = self._evaluate(stmt.prompt)
            prompt = to_veda_text(prompt_value)
            user_text = self.input_fn(prompt)
            try:
                self.env.assign(stmt.name.lexeme, user_text, source=self.source, span=self._span(stmt.name))
            except VedaNameError:
                self.env.define(stmt.name.lexeme, user_text)
            return

        if isinstance(stmt, WhenStatement):
            cond = self._evaluate(stmt.condition)
            branch = stmt.then_branch if self._is_truthy(cond) else (stmt.else_branch or [])
            for inner in branch:
                self._execute(inner)
            return

        if isinstance(stmt, RepeatStatement):
            times_val = self._evaluate(stmt.times)
            n = self._require_number(times_val, token=self._token_from_expr(stmt.times), context="repeat times")
            count = int(n)
            if count < 0:
                raise VedaRuntimeError(
                    "repeat count cannot be negative.",
                    source=self.source,
                    span=self._span(self._token_from_expr(stmt.times)),
                )
            for _ in range(count):
                for inner in stmt.body:
                    self._execute(inner)
            return

        if isinstance(stmt, CountStatement):
            start_val = self._evaluate(stmt.start)
            end_val = self._evaluate(stmt.end)
            start_num = self._require_number(start_val, token=self._token_from_expr(stmt.start), context="count start")
            end_num = self._require_number(end_val, token=self._token_from_expr(stmt.end), context="count end")
            start_i = int(start_num)
            end_i = int(end_num)
            step = 1 if end_i >= start_i else -1
            i = start_i
            while True:
                self.env.define(stmt.name.lexeme, i)
                for inner in stmt.body:
                    self._execute(inner)
                if i == end_i:
                    break
                i += step
            return

        if isinstance(stmt, WorkDeclaration):
            func = VedaFunction(
                name=stmt.name.lexeme,
                params=[p.lexeme for p in stmt.params],
                body=stmt.body,
                closure=self.env,
            )
            self.env.define(stmt.name.lexeme, func)
            return

        if isinstance(stmt, GiveStatement):
            value = self._evaluate(stmt.value)
            raise _ReturnSignal(value)

        if isinstance(stmt, ExpressionStatement):
            self._evaluate(stmt.expression)
            return

        raise RuntimeError(f"Unhandled statement: {stmt!r}")

    # --- Expressions ---
    def _evaluate(self, expr) -> Any:
        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, Identifier):
            return self.env.get(expr.name.lexeme, source=self.source, span=self._span(expr.name))

        if isinstance(expr, UnaryExpression):
            right = self._evaluate(expr.right)
            if expr.operator.type == TokenType.MINUS:
                num = self._require_number(right, token=expr.operator, context="unary '-'")
                return -num
            if expr.operator.type == TokenType.KEYWORD and expr.operator.lexeme == "not":
                return not self._is_truthy(right)
            raise RuntimeError("Unknown unary operator.")

        if isinstance(expr, BinaryExpression):
            op = expr.operator

            if op.type == TokenType.KEYWORD and op.lexeme in ("and", "or"):
                left = self._evaluate(expr.left)
                if op.lexeme == "and":
                    if not self._is_truthy(left):
                        return False
                    right = self._evaluate(expr.right)
                    return self._is_truthy(right)
                if self._is_truthy(left):
                    return True
                right = self._evaluate(expr.right)
                return self._is_truthy(right)

            left = self._evaluate(expr.left)
            right = self._evaluate(expr.right)

            if op.type == TokenType.PLUS:
                if isinstance(left, str) or isinstance(right, str):
                    return to_veda_text(left) + to_veda_text(right)
                return self._require_number(left, token=op, context="+") + self._require_number(
                    right, token=op, context="+"
                )

            if op.type == TokenType.MINUS:
                return self._require_number(left, token=op, context="-") - self._require_number(
                    right, token=op, context="-"
                )

            if op.type == TokenType.STAR:
                return self._require_number(left, token=op, context="*") * self._require_number(
                    right, token=op, context="*"
                )

            if op.type == TokenType.SLASH:
                denominator = self._require_number(right, token=op, context="/")
                if denominator == 0:
                    raise VedaRuntimeError("Division by zero.", source=self.source, span=self._span(op))
                return self._require_number(left, token=op, context="/") / denominator

            if op.type == TokenType.PERCENT:
                denominator = self._require_number(right, token=op, context="%")
                if denominator == 0:
                    raise VedaRuntimeError("Modulo by zero.", source=self.source, span=self._span(op))
                return self._require_number(left, token=op, context="%") % denominator

            if op.type == TokenType.EQUAL_EQUAL:
                return left == right
            if op.type == TokenType.BANG_EQUAL:
                return left != right

            if op.type in (TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS, TokenType.LESS_EQUAL):
                lnum = self._require_number(left, token=op, context="comparison")
                rnum = self._require_number(right, token=op, context="comparison")
                if op.type == TokenType.GREATER:
                    return lnum > rnum
                if op.type == TokenType.GREATER_EQUAL:
                    return lnum >= rnum
                if op.type == TokenType.LESS:
                    return lnum < rnum
                return lnum <= rnum

            raise RuntimeError(f"Unknown binary operator: {op.type}")

        if isinstance(expr, FunctionCall):
            callee = self._evaluate(expr.callee)
            args = [self._evaluate(a) for a in expr.arguments]
            return self._call(callee, args, expr.paren)

        raise RuntimeError(f"Unhandled expression: {expr!r}")

    def _call(self, callee: Any, args: list[Any], paren: Token) -> Any:
        span = self._span(paren)
        if isinstance(callee, BuiltinFunction):
            return callee.call(args, source=self.source, span=span)

        if isinstance(callee, VedaFunction):
            if len(args) != len(callee.params):
                raise VedaTypeError(
                    f"{callee.name}() expected {len(callee.params)} argument(s), got {len(args)}.",
                    source=self.source,
                    span=span,
                )
            local = Environment(values={}, enclosing=callee.closure)
            for name, value in zip(callee.params, args):
                local.define(name, value)

            previous = self.env
            try:
                self.env = local
                for stmt in callee.body:
                    self._execute(stmt)
            except _ReturnSignal as r:
                return r.value
            finally:
                self.env = previous
            return None

        raise VedaTypeError("Can only call functions.", source=self.source, span=span)

    # --- Utilities ---
    def _is_truthy(self, value: Any) -> bool:
        if value is None:
            return False
        if value is False:
            return False
        if value == 0:
            return False
        if value == "":
            return False
        return True

    def _span(self, token: Token) -> SourceSpan:
        return SourceSpan(
            filename=token.filename,
            line=token.line,
            column=token.column,
            length=max(token.length, 1),
        )

    def _require_number(self, value: Any, *, token: Token, context: str) -> float | int:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise VedaTypeError(f"Expected number for {context}.", source=self.source, span=self._span(token))
        return value

    def _token_from_expr(self, expr) -> Token:
        if isinstance(expr, Literal):
            return expr.token
        if isinstance(expr, Identifier):
            return expr.name
        if isinstance(expr, UnaryExpression):
            return expr.operator
        if isinstance(expr, BinaryExpression):
            return expr.operator
        if isinstance(expr, FunctionCall):
            return expr.paren
        return Token(TokenType.EOF, "", None, self.filename, 1, 1, 1)
