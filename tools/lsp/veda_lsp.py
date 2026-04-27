from __future__ import annotations

import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Optional

# Allow running from repo without install
REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "veda"))

from veda.builtins import BuiltinFunction
from veda.checker import Checker
from veda.interpreter import Interpreter
from veda.lexer import Lexer
from veda.parser import Parser


def _collect_definitions(program) -> dict[str, tuple[int, int]]:
    """
    Returns name -> (line0, char0) for declarations.
    """
    from veda.ast_nodes import VariableDeclaration, WorkDeclaration

    defs: dict[str, tuple[int, int]] = {}

    def walk_stmt(stmt) -> None:
        if isinstance(stmt, VariableDeclaration):
            defs.setdefault(stmt.name.lexeme, (stmt.name.line - 1, stmt.name.column - 1))
            return
        if isinstance(stmt, WorkDeclaration):
            defs.setdefault(stmt.name.lexeme, (stmt.name.line - 1, stmt.name.column - 1))
            for inner in stmt.body:
                walk_stmt(inner)
            return

        for attr in ("body", "then_branch", "else_branch"):
            block = getattr(stmt, attr, None)
            if isinstance(block, list):
                for inner in block:
                    walk_stmt(inner)

    for s in getattr(program, "statements", []):
        walk_stmt(s)
    return defs


def _find_identifier_at(tokens, *, line0: int, char0: int) -> Optional[str]:
    for t in tokens:
        if getattr(t, "type", None).name != "IDENTIFIER":
            continue
        if t.line - 1 != line0:
            continue
        start = t.column - 1
        end = start + max(t.length, 1)
        if start <= char0 < end:
            return t.lexeme
    return None


def _read_message() -> Optional[dict]:
    headers: Dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, value = line.decode("utf-8", errors="ignore").split(":", 1)
        headers[key.strip().lower()] = value.strip()

    length = int(headers.get("content-length", "0"))
    body = sys.stdin.buffer.read(length)
    if not body:
        return None
    return json.loads(body.decode("utf-8", errors="ignore"))


def _send(payload: dict) -> None:
    data = json.dumps(payload).encode("utf-8")
    sys.stdout.buffer.write(f"Content-Length: {len(data)}\r\n\r\n".encode("ascii"))
    sys.stdout.buffer.write(data)
    sys.stdout.buffer.flush()


def _publish_diagnostics(uri: str, text: str) -> None:
    tokens, lex_errors = Lexer(text, filename=uri).tokenize_with_errors()
    _, parse_errors = Parser(tokens, source=text, filename=uri).parse_with_errors()
    errors = list(lex_errors) + list(parse_errors)

    if not errors:
        program, _ = Parser(tokens, source=text, filename=uri).parse_with_errors()
        tmp = Interpreter(source=text, filename=uri, output=lambda s: None)
        builtin_names = tmp.builtin_names | {"args"}
        builtin_arity = {
            n: (v.min_arity, v.max_arity) for n, v in tmp.globals.values.items() if isinstance(v, BuiltinFunction)
        }
        errors.extend(Checker(filename=uri, source=text, builtin_names=builtin_names, builtin_arity=builtin_arity).check(program))

    diags = []
    for e in errors:
        start_line = max(e.span.line - 1, 0)
        start_char = max(e.span.column - 1, 0)
        end_char = start_char + max(e.span.length, 1)
        diags.append(
            {
                "range": {
                    "start": {"line": start_line, "character": start_char},
                    "end": {"line": start_line, "character": end_char},
                },
                "severity": 1,
                "message": f"{getattr(e, 'code', '')} {e.message}".strip(),
                "source": "veda",
            }
        )

    _send(
        {
            "jsonrpc": "2.0",
            "method": "textDocument/publishDiagnostics",
            "params": {"uri": uri, "diagnostics": diags},
        }
    )


def main() -> None:
    open_docs: Dict[str, str] = {}
    while True:
        msg = _read_message()
        if msg is None:
            return

        method = msg.get("method")
        if method == "initialize":
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {
                        "capabilities": {
                            "textDocumentSync": 1,
                        }
                    },
                }
            )
            continue

        if method == "shutdown":
            _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": None})
            continue

        if method == "exit":
            return

        if method == "textDocument/didOpen":
            params = msg.get("params", {})
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "<memory>")
            text = doc.get("text", "")
            open_docs[uri] = text
            _publish_diagnostics(uri, text)
            continue

        if method == "textDocument/didChange":
            params = msg.get("params", {})
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "<memory>")
            changes = params.get("contentChanges", [])
            if changes:
                text = changes[-1].get("text", "")
                open_docs[uri] = text
                _publish_diagnostics(uri, text)
            continue

        if method == "textDocument/definition":
            params = msg.get("params", {})
            doc = params.get("textDocument", {})
            uri = doc.get("uri", "<memory>")
            pos = params.get("position", {})
            line0 = int(pos.get("line", 0))
            char0 = int(pos.get("character", 0))
            text = open_docs.get(uri, "")

            try:
                tokens = Lexer(text, filename=uri).tokenize()
                program = Parser(tokens, source=text, filename=uri).parse()
            except Exception:
                _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": None})
                continue

            ident = _find_identifier_at(tokens, line0=line0, char0=char0)
            if not ident:
                _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": None})
                continue

            defs = _collect_definitions(program)
            if ident not in defs:
                _send({"jsonrpc": "2.0", "id": msg.get("id"), "result": None})
                continue

            dline, dchar = defs[ident]
            _send(
                {
                    "jsonrpc": "2.0",
                    "id": msg.get("id"),
                    "result": {
                        "uri": uri,
                        "range": {
                            "start": {"line": dline, "character": dchar},
                            "end": {"line": dline, "character": dchar + len(ident)},
                        },
                    },
                }
            )
            continue


if __name__ == "__main__":
    main()
