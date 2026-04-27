# Progress log (for collaborators)

This is a lightweight “what changed” log so collaborators can quickly understand what’s been built, why it exists, and what to touch next.

Guideline: every meaningful change should add a short entry here (even if it’s only 3–5 bullets).

## 2026-04-27 — Veda v1.0 Stage 0 + Stage 1 improvements

### Stage 0: working interpreter foundation

- Implemented a real interpreter pipeline: lexer → parser → AST → interpreter (no `eval()`/`exec()`).
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

### Docs cleanup (collaborator-friendly)

- Tightened docs to the essentials and rewrote them to sound less “template-generated”.
- Kept only: `docs/syntax.md` (practical guide) and `docs/roadmap.md` (direction).

### Stage 1: “nicer for learners”

- REPL improvements:
  - History support when `readline` is available (arrow keys in many terminals).
  - Simple REPL commands: `:help`, `:history`, `:clear`.
  - Multi-line blocks feel more natural by waiting until `end` closes a block.
- Small standard library additions:
  - Text helpers: `upper(text)`, `lower(text)`, `trim(text)`
  - Math helpers: `abs(number)`, `floor(number)`, `ceil(number)`, `round(number)`
- Friendlier `veda check`:
  - Collects and prints multiple syntax errors in one run (parser recovery via synchronization).
- Windows quality-of-life:
  - UTF‑8 BOM is ignored in the lexer; error printing hides BOM so caret alignment stays sane.

How to try:

- `python main.py run examples/hello.veda`
- `python main.py repl`
- `python main.py check examples/hello.veda`
- `pytest`

