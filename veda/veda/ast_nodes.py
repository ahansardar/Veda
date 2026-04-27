from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional

from veda.token_types import Token


@dataclass
class Program:
    statements: List["Stmt"]


class Stmt:
    pass


class Expr:
    pass


@dataclass
class VariableDeclaration(Stmt):
    name: Token
    initializer: Expr


@dataclass
class Assignment(Stmt):
    name: Token
    value: Expr


@dataclass
class ShowStatement(Stmt):
    expression: Expr


@dataclass
class AskStatement(Stmt):
    name: Token
    prompt: Expr


@dataclass
class WhenStatement(Stmt):
    condition: Expr
    then_branch: List[Stmt]
    else_branch: Optional[List[Stmt]]


@dataclass
class RepeatStatement(Stmt):
    times: Expr
    body: List[Stmt]


@dataclass
class CountStatement(Stmt):
    name: Token
    start: Expr
    end: Expr
    body: List[Stmt]


@dataclass
class WorkDeclaration(Stmt):
    name: Token
    params: List[Token]
    body: List[Stmt]


@dataclass
class GiveStatement(Stmt):
    value: Expr


@dataclass
class ExpressionStatement(Stmt):
    expression: Expr


@dataclass
class BinaryExpression(Expr):
    left: Expr
    operator: Token
    right: Expr


@dataclass
class UnaryExpression(Expr):
    operator: Token
    right: Expr


@dataclass
class Literal(Expr):
    value: Any
    token: Token


@dataclass
class Identifier(Expr):
    name: Token


@dataclass
class FunctionCall(Expr):
    callee: Expr
    paren: Token
    arguments: List[Expr]

