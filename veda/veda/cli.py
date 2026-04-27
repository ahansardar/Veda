from __future__ import annotations

import argparse
import sys
from pathlib import Path
import subprocess

from veda.errors import VedaError
from veda.builtins import BuiltinFunction
from veda.checker import Checker
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser
from veda.repl import Repl


def run_file(path: Path, *, args: list[str] | None = None) -> None:
    source = path.read_text(encoding="utf-8")
    tokens = Lexer(source, filename=str(path)).tokenize()
    program = Parser(tokens, source=source, filename=str(path)).parse()
    interpreter = Interpreter(source=source, filename=str(path))
    interpreter.globals.define("args", list(args or []))
    interpreter.builtin_names.add("args")
    interpreter.run(program)


def check_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tokens, lex_errors = Lexer(source, filename=str(path)).tokenize_with_errors()
    _, parse_errors = Parser(tokens, source=source, filename=str(path)).parse_with_errors()
    errors = lex_errors + parse_errors
    if not errors:
        program, _ = Parser(tokens, source=source, filename=str(path)).parse_with_errors()
        tmp = Interpreter(source=source, filename=str(path), output=lambda s: None)
        builtin_names = tmp.builtin_names | {"args"}
        builtin_arity: dict[str, tuple[int, int | None]] = {}
        for name, value in tmp.globals.values.items():
            if isinstance(value, BuiltinFunction):
                builtin_arity[name] = (value.min_arity, value.max_arity)
        errors.extend(
            Checker(
                filename=str(path),
                source=source,
                builtin_names=builtin_names,
                builtin_arity=builtin_arity,
            ).check(program)
        )

    if errors:
        errors = sorted(errors, key=lambda e: (e.span.line, e.span.column))
        for i, err in enumerate(errors):
            if i:
                print("\n", file=sys.stderr)
            print(err.pretty(), file=sys.stderr)
        print(f"\nFound {len(errors)} error(s).", file=sys.stderr)
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="veda", description="Veda v1.0 - interpreted language")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a .veda file")
    p_run.add_argument("file", help="Path to .veda file")
    p_run.add_argument("args", nargs=argparse.REMAINDER, help="Arguments passed to the program")

    p_check = sub.add_parser("check", help="Lex and parse a .veda file")
    p_check.add_argument("file", help="Path to .veda file")

    sub.add_parser("repl", help="Start Veda REPL")

    p_test = sub.add_parser("test", help="Run the Python test suite (pytest)")
    p_test.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Arguments forwarded to pytest")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "run":
            run_file(Path(args.file), args=args.args)
            return
        if args.cmd == "check":
            check_file(Path(args.file))
            print("OK")
            return
        if args.cmd == "repl":
            Repl().run()
            return
        if args.cmd == "test":
            try:
                cmd = [sys.executable, "-m", "pytest", *args.pytest_args]
                raise SystemExit(subprocess.call(cmd)) from None
            except FileNotFoundError:
                print("pytest is not installed. Try: python -m pip install pytest", file=sys.stderr)
                raise SystemExit(1) from None
    except VedaError as e:
        print(e.pretty(), file=sys.stderr)
        raise SystemExit(1) from None
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        raise SystemExit(1) from None
