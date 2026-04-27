from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

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

    def __init__(self, *, filename: str, source: str, builtin_names: Iterable[str] = ()):
        self.filename = filename
        self.source = source
        self.builtin_names = set(builtin_names)

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

    def _check_statements(self, statements, *, scope: _Scope, in_function: bool, errors: list[VedaCheckError]) -> None:
        for stmt in statements:
            self._check_stmt(stmt, scope=scope, in_function=in_function, errors=errors)

    def _check_stmt(self, stmt, *, scope: _Scope, in_function: bool, errors: list[VedaCheckError]) -> None:
        if isinstance(stmt, VariableDeclaration):
            self._check_expr(stmt.initializer, scope=scope, errors=errors)
            scope.defined.add(stmt.name.lexeme)
            return

        if isinstance(stmt, Assignment):
            if stmt.name.lexeme not in scope.defined:
                errors.append(self._err(stmt.name, f"Assignment to undefined variable '{stmt.name.lexeme}'."))
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
            for p in stmt.params:
                inner.defined.add(p.lexeme)
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

        if isinstance(stmt, ExpressionStatement):
            self._check_expr(stmt.expression, scope=scope, errors=errors)
            return

    def _check_expr(self, expr, *, scope: _Scope, errors: list[VedaCheckError]) -> None:
        if isinstance(expr, Literal):
            return
        if isinstance(expr, Identifier):
            if expr.name.lexeme not in scope.defined:
                errors.append(self._err(expr.name, f"Undefined variable '{expr.name.lexeme}'."))
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
            return
        if isinstance(expr, ListLiteral):
            for item in expr.items:
                self._check_expr(item, scope=scope, errors=errors)
            return
        if isinstance(expr, IndexExpression):
            self._check_expr(expr.target, scope=scope, errors=errors)
            self._check_expr(expr.index, scope=scope, errors=errors)
            return
