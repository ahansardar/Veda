# Veda roadmap



## Stage 0 (current)
- Source → lexer → parser → AST → interpreter
- `veda run`, `veda check`, `veda repl`
- Error messages include filename + line/column + a pointer

## Stage 1 (make it nicer for learners)

- Better REPL experience (history, multi-line blocks that feel natural)
- Small standard library (text helpers, math helpers)
- Friendlier static checks in `veda check` (continue after the first error)

## Stage 2 (performance + packaging)

- Optional bytecode compiler / VM
- A simple module system (importing `.veda` files)
- Packaging story (standard library layout, versioning)

## Stage 3 (self-hosting path)

- Implement a Veda interpreter/compiler in Veda itself
- Keep Stage 0 as a reference implementation and test oracle
