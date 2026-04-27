from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import difflib

from veda.ast_nodes import (
    AskStatement,
    Assignment,
    BinaryExpression,
    CountStatement,
    DictLiteral,
    EachStatement,
    ExpressionStatement,
    FunctionCall,
    GiveStatement,
    Identifier,
    IndexAssignment,
    IndexExpression,
    ListLiteral,
    Literal,
    MemberExpression,
    Program,
    RepeatStatement,
    ShareStatement,
    ShowStatement,
    SliceExpression,
    SliceAssignment,
    StopStatement,
    NextStatement,
    UnaryExpression,
    UseStatement,
    VariableDeclaration,
    WhenStatement,
    WorkDeclaration,
)
from veda.errors import SourceSpan, VedaCheckError
from veda.token_types import Token


@dataclass
class _Scope:
    defined: set[str]

    def copy(self) -> "_Scope":
        return _Scope(defined=set(self.defined))


class Checker:
    """
    Lightweight semantic checks for learners:
    - Use of undefined variables
    - Assignment to undefined variables
    - `give` used outside a `work` function

    This is intentionally conservative. It aims to catch common beginner mistakes
    without implementing a full dataflow/CFG analysis.
    """

    def __init__(
        self,
        *,
        filename: str,
        source: str,
        builtin_names: Iterable[str] = (),
        builtin_arity: dict[str, tuple[int, int | None]] | None = None,
    ):
        self.filename = filename
        self.source = source
        self.builtin_names = set(builtin_names)
        self.builtin_arity = builtin_arity or {}

    def check(self, program: Program) -> list[VedaCheckError]:
        errors: list[VedaCheckError] = []
        scope = _Scope(defined=set(self.builtin_names))
        self._check_statements(program.statements, scope=scope, in_function=False, errors=errors)
        return errors

    def _err(self, token: Token, message: str) -> VedaCheckError:
        return VedaCheckError(
            message,
            source=self.source,
            span=SourceSpan(
                filename=token.filename,
                line=token.line,
                column=token.column,
                length=max(token.length, 1),
            ),
        )

    def _suggest(self, name: str, choices: Iterable[str]) -> str | None:
        match = difflib.get_close_matches(name, sorted(set(choices)), n=1)
        return match[0] if match else None

    def _check_statements(self, statements, *, scope: _Scope, in_function: bool, errors: list[VedaCheckError]) -> None:
        for stmt in statements:
            self._check_stmt(stmt, scope=scope, in_function=in_function, errors=errors)

    def _check_stmt(self, stmt, *, scope: _Scope, in_function: bool, errors: list[VedaCheckError]) -> None:
        if isinstance(stmt, UseStatement):
            return

        if isinstance(stmt, ShareStatement):
            return

        if isinstance(stmt, StopStatement):
            if stmt.condition is not None:
                self._check_expr(stmt.condition, scope=scope, errors=errors)
            return

        if isinstance(stmt, NextStatement):
            if stmt.condition is not None:
                self._check_expr(stmt.condition, scope=scope, errors=errors)
            return

        if isinstance(stmt, VariableDeclaration):
            self._check_expr(stmt.initializer, scope=scope, errors=errors)
            scope.defined.add(stmt.name.lexeme)
            return

        if isinstance(stmt, Assignment):
            if stmt.name.lexeme not in scope.defined:
                sug = self._suggest(stmt.name.lexeme, scope.defined)
                msg = f"Assignment to undefined variable '{stmt.name.lexeme}'."
                if sug:
                    msg += f" Did you mean '{sug}'?"
                errors.append(self._err(stmt.name, msg))
            self._check_expr(stmt.value, scope=scope, errors=errors)
            return

        if isinstance(stmt, IndexAssignment):
            self._check_expr(stmt.target, scope=scope, errors=errors)
            self._check_expr(stmt.index, scope=scope, errors=errors)
            self._check_expr(stmt.value, scope=scope, errors=errors)
            return

        if isinstance(stmt, SliceAssignment):
            self._check_expr(stmt.target, scope=scope, errors=errors)
            if stmt.start is not None:
                self._check_expr(stmt.start, scope=scope, errors=errors)
            if stmt.end is not None:
                self._check_expr(stmt.end, scope=scope, errors=errors)
            self._check_expr(stmt.value, scope=scope, errors=errors)
            return

        if isinstance(stmt, ShowStatement):
            self._check_expr(stmt.expression, scope=scope, errors=errors)
            return

        if isinstance(stmt, AskStatement):
            self._check_expr(stmt.prompt, scope=scope, errors=errors)
            # ask defines if not already defined (runtime behavior), so treat as define.
            scope.defined.add(stmt.name.lexeme)
            return

        if isinstance(stmt, GiveStatement):
            if not in_function:
                errors.append(self._err(stmt.keyword, "give can only be used inside a work function."))
            self._check_expr(stmt.value, scope=scope, errors=errors)
            return

        if isinstance(stmt, WorkDeclaration):
            scope.defined.add(stmt.name.lexeme)
            inner = _Scope(defined=set(scope.defined))
            seen: set[str] = set()
            for p in stmt.params:
                if p.lexeme in seen:
                    errors.append(self._err(p, f"Duplicate parameter name '{p.lexeme}'."))
                seen.add(p.lexeme)
                inner.defined.add(p.lexeme)

            # Unreachable code after give (simple linear check).
            returned = False
            for s in stmt.body:
                if returned:
                    # keep the message gentle; this is for learners.
                    token = getattr(s, "name", None) or getattr(s, "keyword", None) or stmt.name
                    errors.append(self._err(token, "Unreachable code after give."))  # type: ignore[arg-type]
                    break
                if isinstance(s, GiveStatement):
                    returned = True

            self._check_statements(stmt.body, scope=inner, in_function=True, errors=errors)
            return

        if isinstance(stmt, WhenStatement):
            self._check_expr(stmt.condition, scope=scope, errors=errors)
            then_scope = scope.copy()
            self._check_statements(stmt.then_branch, scope=then_scope, in_function=in_function, errors=errors)

            if stmt.else_branch is not None:
                else_scope = scope.copy()
                self._check_statements(stmt.else_branch, scope=else_scope, in_function=in_function, errors=errors)
                # Only keep variables defined in both branches.
                scope.defined = scope.defined.union(then_scope.defined.intersection(else_scope.defined))
            else:
                # No else: definitions are not guaranteed.
                scope.defined = scope.defined.union(scope.defined)
            return

        if isinstance(stmt, RepeatStatement):
            self._check_expr(stmt.times, scope=scope, errors=errors)
            body_scope = scope.copy()
            self._check_statements(stmt.body, scope=body_scope, in_function=in_function, errors=errors)
            return

        if isinstance(stmt, CountStatement):
            self._check_expr(stmt.start, scope=scope, errors=errors)
            self._check_expr(stmt.end, scope=scope, errors=errors)
            body_scope = scope.copy()
            body_scope.defined.add(stmt.name.lexeme)
            self._check_statements(stmt.body, scope=body_scope, in_function=in_function, errors=errors)
            return

        if isinstance(stmt, EachStatement):
            self._check_expr(stmt.iterable, scope=scope, errors=errors)
            body_scope = scope.copy()
            body_scope.defined.add(stmt.name.lexeme)
            if stmt.second_name is not None:
                body_scope.defined.add(stmt.second_name.lexeme)
            self._check_statements(stmt.body, scope=body_scope, in_function=in_function, errors=errors)
            return

        if isinstance(stmt, ExpressionStatement):
            self._check_expr(stmt.expression, scope=scope, errors=errors)
            return

    def _check_expr(self, expr, *, scope: _Scope, errors: list[VedaCheckError]) -> None:
        if isinstance(expr, Literal):
            return
        if isinstance(expr, Identifier):
            if expr.name.lexeme not in scope.defined:
                sug = self._suggest(expr.name.lexeme, scope.defined)
                msg = f"Undefined variable '{expr.name.lexeme}'."
                if sug:
                    msg += f" Did you mean '{sug}'?"
                errors.append(self._err(expr.name, msg))
            return
        if isinstance(expr, UnaryExpression):
            self._check_expr(expr.right, scope=scope, errors=errors)
            return
        if isinstance(expr, BinaryExpression):
            self._check_expr(expr.left, scope=scope, errors=errors)
            self._check_expr(expr.right, scope=scope, errors=errors)
            return
        if isinstance(expr, FunctionCall):
            self._check_expr(expr.callee, scope=scope, errors=errors)
            for a in expr.arguments:
                self._check_expr(a, scope=scope, errors=errors)

            # Builtin arity check (only when calling by name, e.g. len(x)).
            if isinstance(expr.callee, Identifier):
                name = expr.callee.name.lexeme
                if name in self.builtin_arity:
                    min_a, max_a = self.builtin_arity[name]
                    got = len(expr.arguments)
                    if got < min_a or (max_a is not None and got > max_a):
                        if max_a is None:
                            msg = f"{name}() expects at least {min_a} argument(s), got {got}."
                        elif min_a == max_a:
                            msg = f"{name}() expects {min_a} argument(s), got {got}."
                        else:
                            msg = f"{name}() expects {min_a}..{max_a} argument(s), got {got}."
                        errors.append(self._err(expr.paren, msg))
            return
        if isinstance(expr, ListLiteral):
            for item in expr.items:
                self._check_expr(item, scope=scope, errors=errors)
            return
        if isinstance(expr, DictLiteral):
            for k, v in expr.pairs:
                self._check_expr(k, scope=scope, errors=errors)
                self._check_expr(v, scope=scope, errors=errors)
            return
        if isinstance(expr, IndexExpression):
            self._check_expr(expr.target, scope=scope, errors=errors)
            self._check_expr(expr.index, scope=scope, errors=errors)
            return
        if isinstance(expr, SliceExpression):
            self._check_expr(expr.target, scope=scope, errors=errors)
            if expr.start is not None:
                self._check_expr(expr.start, scope=scope, errors=errors)
            if expr.end is not None:
                self._check_expr(expr.end, scope=scope, errors=errors)
            return
        if isinstance(expr, MemberExpression):
            self._check_expr(expr.target, scope=scope, errors=errors)
            return
