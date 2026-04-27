from __future__ import annotations

import argparse
import sys
from pathlib import Path

from veda.errors import VedaError
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser
from veda.repl import Repl


def run_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tokens = Lexer(source, filename=str(path)).tokenize()
    program = Parser(tokens, source=source, filename=str(path)).parse()
    Interpreter(source=source, filename=str(path)).run(program)


def check_file(path: Path) -> None:
    source = path.read_text(encoding="utf-8")
    tokens = Lexer(source, filename=str(path)).tokenize()
    Parser(tokens, source=source, filename=str(path)).parse()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="veda", description="Veda v1.0 - interpreted language")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Run a .veda file")
    p_run.add_argument("file", help="Path to .veda file")

    p_check = sub.add_parser("check", help="Lex and parse a .veda file")
    p_check.add_argument("file", help="Path to .veda file")

    sub.add_parser("repl", help="Start Veda REPL")

    args = parser.parse_args(argv)

    try:
        if args.cmd == "run":
            run_file(Path(args.file))
            return
        if args.cmd == "check":
            check_file(Path(args.file))
            print("OK")
            return
        if args.cmd == "repl":
            Repl().run()
            return
    except VedaError as e:
        print(e.pretty(), file=sys.stderr)
        raise SystemExit(1) from None
    except FileNotFoundError:
        print(f"File not found: {args.file}", file=sys.stderr)
        raise SystemExit(1) from None

