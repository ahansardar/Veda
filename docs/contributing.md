# Contributing

This repo is intentionally modular so collaborators can work without stepping on each other.

## Setup

```bash
pip install -e .
pip install pytest
```

## Tests

```bash
pytest
```

Or:

```bash
veda test
```

## Where things live

- Lexer: `veda/veda/lexer.py`
- Parser + AST: `veda/veda/parser.py`, `veda/veda/ast_nodes.py`
- Interpreter/runtime: `veda/veda/interpreter.py`, `veda/veda/environment.py`
- Static checks: `veda/veda/checker.py`
- CLI: `veda/veda/cli.py`
- REPL: `veda/veda/repl.py`

## Collaboration workflow

- Keep changes focused.
- Update `docs/progress.md` on every meaningful change.
- Add tests when you add syntax or runtime behavior.

