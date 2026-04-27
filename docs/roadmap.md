# Roadmap

This repo is the “Stage 0/1” reference interpreter: clarity first, with tooling that makes it nice for learners and collaborators.

## Stage 0 (foundation)

- Source → lexer → parser → AST → interpreter (no `eval()`/`exec()`)
- `veda run`, `veda check`, `veda repl`
- Useful error messages with filename + line/column + underline pointer

## Stage 1 (learner-friendly, but real-world usable)

- REPL that feels good:
  - history, multiline blocks, introspection (`:type`, `:doc`, `:check`, etc.)
- Language ergonomics:
  - loop control (`stop`, `next` + optional `when`)
  - collections (`list`, `map`, `set`), slicing, and index assignment
  - modules: file modules + stdlib modules, caching, exports (`share`), namespacing, circular detection
  - text interpolation and multi-line strings
- Standard library:
  - text/math/random/time/fs helpers
  - higher-order list helpers (`map_values`, `filter`, `reduce`)
- Safety:
  - safe mode for running untrusted scripts (`--safe`, `--allow-root`)
- Tooling:
  - formatter (`veda fmt`) and linter (`veda lint`)
  - VS Code syntax highlighting + tiny LSP prototype
- Quality:
  - `veda check` continues after errors + adds semantic checks
  - golden tests for diagnostics + fuzz tests + GitHub Actions CI
- Performance:
  - constant folding and other fast paths
  - (optional) bytecode VM belongs here if we keep it optional

## Stage 2 (packaging + scale)

- Module packaging story (stdlib layout, versioning)
- Standard library modules as first-class packages
- Better performance work (resolver for locals, caching, etc.)

## Stage 3 (self-hosting path)

- Implement a Veda interpreter/compiler in Veda
- Keep this Stage 0/1 interpreter as a reference + test oracle

