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
from veda.options import InterpreterOptions
from veda.parser import Parser
from veda.repl import Repl
from veda.formatter import format_source
from veda.linter import fix_source, lint_source


def run_file(path: Path, *, args: list[str] | None = None, options: InterpreterOptions | None = None) -> None:
    source = path.read_text(encoding="utf-8")
    tokens = Lexer(source, filename=str(path)).tokenize()
    program = Parser(tokens, source=source, filename=str(path)).parse()
    interpreter = Interpreter(source=source, filename=str(path), options=options)
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
    p_run.add_argument("--safe", action="store_true", help="Enable safe mode (restrict file access)")
    p_run.add_argument(
        "--allow-root",
        action="append",
        default=[],
        help="Allowed root directory for safe mode (repeatable)",
    )

    p_check = sub.add_parser("check", help="Lex and parse a .veda file")
    p_check.add_argument("file", help="Path to .veda file")

    p_repl = sub.add_parser("repl", help="Start Veda REPL")
    p_repl.add_argument("--safe", action="store_true", help="Enable safe mode (restrict file access)")
    p_repl.add_argument(
        "--allow-root",
        action="append",
        default=[],
        help="Allowed root directory for safe mode (repeatable)",
    )

    p_test = sub.add_parser("test", help="Run the Python test suite (pytest)")
    p_test.add_argument("pytest_args", nargs=argparse.REMAINDER, help="Arguments forwarded to pytest")

    p_fmt = sub.add_parser("fmt", help="Format a .veda file (indentation)")
    p_fmt.add_argument("file", help="Path to .veda file")
    p_fmt.add_argument("--check", action="store_true", help="Exit with non-zero if changes are needed")

    p_lint = sub.add_parser("lint", help="Lint a .veda file (style checks)")
    p_lint.add_argument("file", help="Path to .veda file")
    p_lint.add_argument("--fix", action="store_true", help="Auto-fix basic issues in-place")

    args, unknown = parser.parse_known_args(argv)

    try:
        if args.cmd == "run":
            options = InterpreterOptions(safe_mode=args.safe, allowed_roots=[Path(p) for p in args.allow_root])
            program_args = unknown
            if program_args and program_args[0] == "--":
                program_args = program_args[1:]
            run_file(Path(args.file), args=program_args, options=options)
            return
        if args.cmd == "check":
            if unknown:
                raise SystemExit(2)
            check_file(Path(args.file))
            print("OK")
            return
        if args.cmd == "repl":
            if unknown:
                raise SystemExit(2)
            options = InterpreterOptions(safe_mode=args.safe, allowed_roots=[Path(p) for p in args.allow_root])
            Repl(options=options).run()
            return
        if args.cmd == "test":
            try:
                cmd = [sys.executable, "-m", "pytest", *args.pytest_args]
                raise SystemExit(subprocess.call(cmd)) from None
            except FileNotFoundError:
                print("pytest is not installed. Try: python -m pip install pytest", file=sys.stderr)
                raise SystemExit(1) from None
        if args.cmd == "fmt":
            if unknown:
                raise SystemExit(2)
            path = Path(args.file)
            source = path.read_text(encoding="utf-8")
            result = format_source(source)
            if args.check:
                raise SystemExit(1 if result.changed else 0) from None
            if result.changed:
                path.write_text(result.formatted, encoding="utf-8")
                print("Formatted.")
            else:
                print("Already formatted.")
            return
        if args.cmd == "lint":
            if unknown:
                raise SystemExit(2)
            path = Path(args.file)
            source = path.read_text(encoding="utf-8")
            if args.fix:
                fixed = fix_source(source)
                if fixed != source:
                    path.write_text(fixed, encoding="utf-8")
                    source = fixed
            issues = lint_source(source)
            if not issues:
                print("OK")
                return
            for it in issues:
                print(f"{path}:{it.line}:{it.column} {it.code} {it.message}", file=sys.stderr)
            raise SystemExit(1) from None
    except VedaError as e:
        print(e.pretty(), file=sys.stderr)
        raise SystemExit(1) from None
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        raise SystemExit(1) from None
