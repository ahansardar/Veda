# Progress log 

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


### Stage 1: “nicer for learners”

- REPL improvements:
  - History support when `readline` is available (arrow keys in many terminals).
  - Optional “pro” editing with `prompt_toolkit` (install via `pip install -e .[repl]`).
  - Simple REPL commands: `:help`, `:history`, `:clear`, `:vars`, `:reset`, `:load <file.veda>`.
  - Multi-line blocks feel more natural by waiting until `end` closes a block.
- Small standard library additions:
  - Text helpers: `upper(text)`, `lower(text)`, `trim(text)`
  - More text helpers: `replace(text, old, new)`, `contains(text, part)`, `starts(text, prefix)`, `ends(text, suffix)`,
    `find(text, part)`, `slice(text, start, end)`, `repeat_text(text, times)`
  - More math helpers: `abs(number)`, `floor(number)`, `ceil(number)`, `round(number)`, `sqrt(number)`, `pow(a, b)`,
    `min(a, b)`, `max(a, b)`, `clamp(value, lo, hi)`
  - Math constants: `pi`, `e`
- Friendlier `veda check`:
  - Collects and prints multiple syntax errors in one run (parser recovery via synchronization).
  - Also collects lexer errors (best-effort) instead of stopping at the first unexpected character.
- Windows quality-of-life:
  - UTF‑8 BOM is ignored in the lexer; error printing hides BOM so caret alignment stays sane.

How to try:

- `python main.py run examples/hello.veda`
- `python main.py repl`
- `python main.py check examples/hello.veda`
- `pytest`
