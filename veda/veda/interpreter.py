from __future__ import annotations

import math
import os
import random
import time
from dataclasses import dataclass
from pathlib import Path
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
    IndexExpression,
    ListLiteral,
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
from veda.lexer import Lexer
from veda.parser import Parser
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
        self.builtin_names: set[str] = set()
        self._call_depth = 0
        self._install_builtins()

    def _install_builtins(self) -> None:
        def _len(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, str):
                return len(value)
            if isinstance(value, list):
                return len(value)
            raise VedaTypeError("len() expects text or list.", source=source, span=span)

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
            # Beginner-friendly rounding: halves go away from zero (2.5 -> 3, -2.5 -> -3).
            if value >= 0:
                return math.floor(value + 0.5)
            return math.ceil(value - 0.5)

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

        def _replace(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, old, new = args
            if not isinstance(text, str) or not isinstance(old, str) or not isinstance(new, str):
                raise VedaTypeError("replace() expects (text, text, text).", source=source, span=span)
            return text.replace(old, new)

        def _contains(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, part = args
            if not isinstance(text, str) or not isinstance(part, str):
                raise VedaTypeError("contains() expects (text, text).", source=source, span=span)
            return part in text

        def _starts(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, prefix = args
            if not isinstance(text, str) or not isinstance(prefix, str):
                raise VedaTypeError("starts() expects (text, text).", source=source, span=span)
            return text.startswith(prefix)

        def _ends(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, suffix = args
            if not isinstance(text, str) or not isinstance(suffix, str):
                raise VedaTypeError("ends() expects (text, text).", source=source, span=span)
            return text.endswith(suffix)

        def _find(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, part = args
            if not isinstance(text, str) or not isinstance(part, str):
                raise VedaTypeError("find() expects (text, text).", source=source, span=span)
            return text.find(part)

        def _slice(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, start, end = args
            if not isinstance(text, str):
                raise VedaTypeError("slice() expects text as first argument.", source=source, span=span)
            if isinstance(start, bool) or not isinstance(start, (int, float)):
                raise VedaTypeError("slice() expects start as a number.", source=source, span=span)
            if isinstance(end, bool) or not isinstance(end, (int, float)):
                raise VedaTypeError("slice() expects end as a number.", source=source, span=span)
            return text[int(start) : int(end)]

        def _repeat_text(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, times = args
            if not isinstance(text, str):
                raise VedaTypeError("repeat_text() expects text as first argument.", source=source, span=span)
            if isinstance(times, bool) or not isinstance(times, (int, float)):
                raise VedaTypeError("repeat_text() expects times as a number.", source=source, span=span)
            n = int(times)
            if n < 0:
                raise VedaTypeError("repeat_text() expects a non-negative times value.", source=source, span=span)
            return text * n

        def _sqrt(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("sqrt() expects a number value.", source=source, span=span)
            if value < 0:
                raise VedaTypeError("sqrt() cannot take a negative number.", source=source, span=span)
            return math.sqrt(value)

        def _pow(args: list[Any], source: str, span: SourceSpan) -> Any:
            a, b = args
            if isinstance(a, bool) or not isinstance(a, (int, float)):
                raise VedaTypeError("pow() expects numbers.", source=source, span=span)
            if isinstance(b, bool) or not isinstance(b, (int, float)):
                raise VedaTypeError("pow() expects numbers.", source=source, span=span)
            return a**b

        def _min2(args: list[Any], source: str, span: SourceSpan) -> Any:
            a, b = args
            if isinstance(a, bool) or not isinstance(a, (int, float)):
                raise VedaTypeError("min() expects numbers.", source=source, span=span)
            if isinstance(b, bool) or not isinstance(b, (int, float)):
                raise VedaTypeError("min() expects numbers.", source=source, span=span)
            return a if a <= b else b

        def _max2(args: list[Any], source: str, span: SourceSpan) -> Any:
            a, b = args
            if isinstance(a, bool) or not isinstance(a, (int, float)):
                raise VedaTypeError("max() expects numbers.", source=source, span=span)
            if isinstance(b, bool) or not isinstance(b, (int, float)):
                raise VedaTypeError("max() expects numbers.", source=source, span=span)
            return a if a >= b else b

        def _clamp(args: list[Any], source: str, span: SourceSpan) -> Any:
            value, lo, hi = args
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("clamp() expects numbers.", source=source, span=span)
            if isinstance(lo, bool) or not isinstance(lo, (int, float)):
                raise VedaTypeError("clamp() expects numbers.", source=source, span=span)
            if isinstance(hi, bool) or not isinstance(hi, (int, float)):
                raise VedaTypeError("clamp() expects numbers.", source=source, span=span)
            if lo > hi:
                raise VedaTypeError("clamp() expects lo <= hi.", source=source, span=span)
            return hi if value > hi else (lo if value < lo else value)

        def _split(args: list[Any], source: str, span: SourceSpan) -> Any:
            text, sep = args
            if not isinstance(text, str) or not isinstance(sep, str):
                raise VedaTypeError("split() expects (text, text).", source=source, span=span)
            if sep == "":
                raise VedaTypeError("split() separator cannot be empty.", source=source, span=span)
            return text.split(sep)

        def _join(args: list[Any], source: str, span: SourceSpan) -> Any:
            items, sep = args
            if not isinstance(items, list) or not isinstance(sep, str):
                raise VedaTypeError("join() expects (list, text).", source=source, span=span)
            return sep.join(to_veda_text(x) for x in items)

        def _push(args: list[Any], source: str, span: SourceSpan) -> Any:
            items, value = args
            if not isinstance(items, list):
                raise VedaTypeError("push() expects a list as first argument.", source=source, span=span)
            items.append(value)
            return None

        def _pop(args: list[Any], source: str, span: SourceSpan) -> Any:
            items = args[0]
            if not isinstance(items, list):
                raise VedaTypeError("pop() expects a list.", source=source, span=span)
            if not items:
                raise VedaRuntimeError("pop() on empty list.", source=source, span=span)
            return items.pop()

        def _insert(args: list[Any], source: str, span: SourceSpan) -> Any:
            items, index, value = args
            if not isinstance(items, list):
                raise VedaTypeError("insert() expects a list as first argument.", source=source, span=span)
            if isinstance(index, bool) or not isinstance(index, (int, float)):
                raise VedaTypeError("insert() expects index as a number.", source=source, span=span)
            items.insert(int(index), value)
            return None

        def _remove_at(args: list[Any], source: str, span: SourceSpan) -> Any:
            items, index = args
            if not isinstance(items, list):
                raise VedaTypeError("remove_at() expects a list as first argument.", source=source, span=span)
            if isinstance(index, bool) or not isinstance(index, (int, float)):
                raise VedaTypeError("remove_at() expects index as a number.", source=source, span=span)
            i = int(index)
            if i < 0 or i >= len(items):
                raise VedaRuntimeError("remove_at() index out of range.", source=source, span=span)
            return items.pop(i)

        def _range_list(args: list[Any], source: str, span: SourceSpan) -> Any:
            start, end = args
            if isinstance(start, bool) or not isinstance(start, (int, float)):
                raise VedaTypeError("range() expects numbers.", source=source, span=span)
            if isinstance(end, bool) or not isinstance(end, (int, float)):
                raise VedaTypeError("range() expects numbers.", source=source, span=span)
            a = int(start)
            b = int(end)
            step = 1 if b >= a else -1
            out: list[int] = []
            i = a
            while True:
                out.append(i)
                if i == b:
                    break
                i += step
            return out

        def _rand(args: list[Any], source: str, span: SourceSpan) -> Any:
            return random.random()

        def _randint(args: list[Any], source: str, span: SourceSpan) -> Any:
            lo, hi = args
            if isinstance(lo, bool) or not isinstance(lo, (int, float)):
                raise VedaTypeError("randint() expects numbers.", source=source, span=span)
            if isinstance(hi, bool) or not isinstance(hi, (int, float)):
                raise VedaTypeError("randint() expects numbers.", source=source, span=span)
            return random.randint(int(lo), int(hi))

        def _seed(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("seed() expects a number.", source=source, span=span)
            random.seed(int(value))
            return None

        def _now_ms(args: list[Any], source: str, span: SourceSpan) -> Any:
            return int(time.time() * 1000)

        def _sleep_ms(args: list[Any], source: str, span: SourceSpan) -> Any:
            value = args[0]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise VedaTypeError("sleep_ms() expects a number.", source=source, span=span)
            ms = float(value)
            if ms < 0:
                raise VedaTypeError("sleep_ms() cannot be negative.", source=source, span=span)
            time.sleep(ms / 1000.0)
            return None

        def _read_file(args: list[Any], source: str, span: SourceSpan) -> Any:
            path = args[0]
            if not isinstance(path, str):
                raise VedaTypeError("read_file() expects a text path.", source=source, span=span)
            try:
                return Path(path).read_text(encoding="utf-8")
            except Exception as e:
                raise VedaRuntimeError("Could not read file.", source=source, span=span) from e

        def _write_file(args: list[Any], source: str, span: SourceSpan) -> Any:
            path, text = args
            if not isinstance(path, str) or not isinstance(text, str):
                raise VedaTypeError("write_file() expects (text, text).", source=source, span=span)
            try:
                Path(path).write_text(text, encoding="utf-8")
            except Exception as e:
                raise VedaRuntimeError("Could not write file.", source=source, span=span) from e
            return None

        def _cwd(args: list[Any], source: str, span: SourceSpan) -> Any:
            return os.getcwd()

        def _panic(args: list[Any], source: str, span: SourceSpan) -> Any:
            msg = args[0]
            raise VedaRuntimeError(to_veda_text(msg), source=source, span=span)

        def _include(args: list[Any], source: str, span: SourceSpan) -> Any:
            path_value = args[0]
            if not isinstance(path_value, str):
                raise VedaTypeError("include() expects a text path.", source=source, span=span)

            base: Path | None = None
            if self.filename and not self.filename.startswith("<"):
                try:
                    base = Path(self.filename).resolve().parent
                except Exception:
                    base = None

            path = Path(path_value)
            if not path.is_absolute() and base is not None:
                path = base / path

            try:
                included_source = path.read_text(encoding="utf-8")
            except Exception as e:
                raise VedaRuntimeError("Could not read included file.", source=source, span=span) from e

            tokens = Lexer(included_source, filename=str(path)).tokenize()
            program = Parser(tokens, source=included_source, filename=str(path)).parse()

            old_source = self.source
            old_filename = self.filename
            try:
                self.source = included_source
                self.filename = str(path)
                self.run(program)
            finally:
                self.source = old_source
                self.filename = old_filename
            return None

        self.globals.define("replace", BuiltinFunction("replace", _replace, min_arity=3, max_arity=3))
        self.globals.define("contains", BuiltinFunction("contains", _contains, min_arity=2, max_arity=2))
        self.globals.define("starts", BuiltinFunction("starts", _starts, min_arity=2, max_arity=2))
        self.globals.define("ends", BuiltinFunction("ends", _ends, min_arity=2, max_arity=2))
        self.globals.define("find", BuiltinFunction("find", _find, min_arity=2, max_arity=2))
        self.globals.define("slice", BuiltinFunction("slice", _slice, min_arity=3, max_arity=3))
        self.globals.define("repeat_text", BuiltinFunction("repeat_text", _repeat_text, min_arity=2, max_arity=2))
        self.globals.define("split", BuiltinFunction("split", _split, min_arity=2, max_arity=2))
        self.globals.define("join", BuiltinFunction("join", _join, min_arity=2, max_arity=2))
        self.globals.define("push", BuiltinFunction("push", _push, min_arity=2, max_arity=2))
        self.globals.define("pop", BuiltinFunction("pop", _pop, min_arity=1, max_arity=1))
        self.globals.define("insert", BuiltinFunction("insert", _insert, min_arity=3, max_arity=3))
        self.globals.define("remove_at", BuiltinFunction("remove_at", _remove_at, min_arity=2, max_arity=2))
        self.globals.define("range", BuiltinFunction("range", _range_list, min_arity=2, max_arity=2))
        self.globals.define("rand", BuiltinFunction("rand", _rand, min_arity=0, max_arity=0))
        self.globals.define("randint", BuiltinFunction("randint", _randint, min_arity=2, max_arity=2))
        self.globals.define("seed", BuiltinFunction("seed", _seed, min_arity=1, max_arity=1))
        self.globals.define("now_ms", BuiltinFunction("now_ms", _now_ms, min_arity=0, max_arity=0))
        self.globals.define("sleep_ms", BuiltinFunction("sleep_ms", _sleep_ms, min_arity=1, max_arity=1))
        self.globals.define("read_file", BuiltinFunction("read_file", _read_file, min_arity=1, max_arity=1))
        self.globals.define("write_file", BuiltinFunction("write_file", _write_file, min_arity=2, max_arity=2))
        self.globals.define("cwd", BuiltinFunction("cwd", _cwd, min_arity=0, max_arity=0))
        self.globals.define("panic", BuiltinFunction("panic", _panic, min_arity=1, max_arity=1))
        self.globals.define("include", BuiltinFunction("include", _include, min_arity=1, max_arity=1))
        self.globals.define("sqrt", BuiltinFunction("sqrt", _sqrt, min_arity=1, max_arity=1))
        self.globals.define("pow", BuiltinFunction("pow", _pow, min_arity=2, max_arity=2))
        self.globals.define("min", BuiltinFunction("min", _min2, min_arity=2, max_arity=2))
        self.globals.define("max", BuiltinFunction("max", _max2, min_arity=2, max_arity=2))
        self.globals.define("clamp", BuiltinFunction("clamp", _clamp, min_arity=3, max_arity=3))

        self.globals.define("pi", math.pi)
        self.globals.define("e", math.e)

        self.builtin_names.update(
            {
                "len",
                "type",
                "text",
                "num",
                "upper",
                "lower",
                "trim",
                "abs",
                "floor",
                "ceil",
                "round",
                "replace",
                "contains",
                "starts",
                "ends",
                "find",
                "slice",
                "repeat_text",
                "split",
                "join",
                "push",
                "pop",
                "insert",
                "remove_at",
                "range",
                "rand",
                "randint",
                "seed",
                "now_ms",
                "sleep_ms",
                "read_file",
                "write_file",
                "cwd",
                "panic",
                "include",
                "sqrt",
                "pow",
                "min",
                "max",
                "clamp",
                "pi",
                "e",
            }
        )

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
            if self._call_depth <= 0:
                raise VedaRuntimeError(
                    "give can only be used inside a work function.",
                    source=self.source,
                    span=self._span(stmt.keyword),
                )
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

        if isinstance(expr, ListLiteral):
            return [self._evaluate(item) for item in expr.items]

        if isinstance(expr, IndexExpression):
            target = self._evaluate(expr.target)
            index_val = self._evaluate(expr.index)
            if isinstance(index_val, bool) or not isinstance(index_val, (int, float)):
                raise VedaTypeError(
                    "Index must be a number.",
                    source=self.source,
                    span=self._span(expr.bracket),
                )
            i = int(index_val)

            if isinstance(target, list):
                if i < 0 or i >= len(target):
                    raise VedaRuntimeError(
                        "List index out of range.",
                        source=self.source,
                        span=self._span(expr.bracket),
                    )
                return target[i]

            if isinstance(target, str):
                if i < 0 or i >= len(target):
                    raise VedaRuntimeError(
                        "Text index out of range.",
                        source=self.source,
                        span=self._span(expr.bracket),
                    )
                return target[i]

            raise VedaTypeError(
                "Can only index lists or text.",
                source=self.source,
                span=self._span(expr.bracket),
            )

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
                self._call_depth += 1
                for stmt in callee.body:
                    self._execute(stmt)
            except _ReturnSignal as r:
                return r.value
            finally:
                self._call_depth -= 1
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
