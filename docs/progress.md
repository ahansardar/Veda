# Progress log

This is a lightweight "what changed" log so collaborators can quickly understand what has been built, why it exists, and what to touch next.

Guideline: every meaningful change should add a short entry here (even if it is only 3-5 bullets).

## 2026-04-27 - Veda v1.0 Stage 0 + Stage 1 (extensive)

### Stage 0: working interpreter foundation

- Implemented a real interpreter pipeline: lexer -> parser -> AST -> interpreter (no `eval()`/`exec()`).
- Added CLI commands: `veda run`, `veda check`, `veda repl`.
- Implemented core language features: variables, reassignment, `show`, `ask`, `when/else`, `repeat`, `count`, `work/give`, operators, truthiness, and nested environments.
- Added examples in `examples/` and pytest coverage in `tests/`.

Key files:

- `veda/veda/lexer.py`
- `veda/veda/parser.py`
- `veda/veda/ast_nodes.py`
- `veda/veda/interpreter.py`
- `veda/veda/environment.py`
- `veda/veda/cli.py`
- `veda/veda/repl.py`

### Stage 1: nicer for learners

- REPL improvements:
  - History support when `readline` is available.
  - Optional "pro" editing with `prompt_toolkit` (install via `pip install -e .[repl]`).
  - Simple REPL commands: `:help`, `:history`, `:clear`, `:vars`, `:reset`, `:load <file.veda>`.
  - Multi-line blocks: the REPL waits until `end` closes a block.
- Friendlier checks:
  - `veda check` collects and prints multiple lexer/parser errors (best-effort) instead of stopping at the first.
  - Adds semantic checks (undefined vars, `give` outside `work`, common builtin mistakes, etc.).
- Standard library (expanded): text + math helpers, collections helpers, random/time, and optional safe file IO.
- Tooling:
  - `veda fmt` (canonical indentation) and `veda lint` (beginner-friendly style rules).
  - `veda test` runs the pytest suite.
- Error UX:
  - Error codes (V001/V101/V201/V300/V401), full-span highlights, and "did you mean...?" suggestions.
  - Runtime stack traces include function locations and argument previews.
- Language growth (still Stage 1):
  - Loop control: `stop` / `next` (also `stop when ...`, `next when ...`).
  - `each` loops, modules (`use math`, `use "./file.veda"`), `share` exports, and circular import detection.
  - Collections: list/map literals, indexing, slicing, and assignment.
  - Extra literals/features: `none`, multi-line text (`""" ... """`), and text interpolation (`"Hello {name}"`).

### Stage 1: VS Code extension packaging

- Added snippets and a Veda file icon theme to the VS Code extension.
- Packaging is done via `npx @vscode/vsce package -o dist` from `tools/vscode`.

Key files:

- `tools/vscode/package.json`
- `tools/vscode/themes/veda-icon-theme.json`
- `tools/vscode/icons/veda-file.svg`
- `tools/vscode/icons/veda-extension.png`
- `tools/vscode/snippets/veda.json`

How to try:

- `python main.py run examples/hello.veda`
- `python main.py repl`
- `python main.py check examples/hello.veda`
- `pytest`
