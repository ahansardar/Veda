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

### Stage 1

- Data types:
  - `list` literals: `[1, 2, 3]`, indexing `a[0]`, slicing `a[1:3]`, index assignment `a[0] = 99`
  - `map` literals: `{"name": "Ahan"}`, indexing `m["name"]`, assignment `m["k"] = v`
  - Indexing also works on text: `"hello"[1]` and `"hello"[1:4]`
- Language additions:
  - `each x in iterable do ... end` (iterates lists, text characters, or map keys)
  - `use "file.veda"` runs another file once (cached); `include("file.veda")` runs every time
  - Text interpolation: `"Hello {name}"` (use `{{` / `}}` for literal braces)
  - Multi-line text: `""" ... """`
- Standard library (expanded):
  - Lists: `push`, `pop`, `insert`, `remove_at`, `copy`, `reverse`, `sort`, `range`
  - Maps: `keys`, `values`, `has_key`, `get`, `del_key`
  - Text: `split`, `join`, plus earlier helpers like `replace/contains/...`
  - Random + time: `rand`, `randint`, `seed`, `choice`, `shuffle`, `now_ms`, `sleep_ms`
  - Files + paths: `read_file`, `read_lines`, `write_file`, `write_lines`, `append_file`, `exists`, `ls`, `mkdir`,
    `cwd`, `path_join`, `basename`, `dirname`
  - Math: `sin/cos/tan/log/exp` added (in addition to `sqrt/pow/...`)
  - Debug: `panic(message)`
- `veda check` is now more helpful:
  - Collects lexer + parser errors (best-effort) instead of stopping at the first issue
  - Adds semantic checks (undefined vars, assignment before `make`, `give` outside `work`, builtin arity mistakes, etc.)
- Errors:
  - Underlines full token spans
  - Runtime errors include a simple Veda stack trace for function calls
- Contributor ergonomics:
  - `veda test` runs the Python pytest suite
  - REPL introspection commands: `:tokens`, `:ast`, `:type`, `:doc`, `:check`, plus `:save`/`:loadenv`

How to try:

- `python main.py run examples/hello.veda`
- `python main.py repl`
- `python main.py check examples/hello.veda`
- `pytest`
