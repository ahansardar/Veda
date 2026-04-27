# Standard library (v1.0 Stage 1)

Veda’s “stdlib” is currently a set of built-in functions plus a few built-in modules.

## Built-in modules

- `use math` → numeric helpers
- `use text` → text helpers
- `use random` → random helpers
- `use time` → time helpers
- `use fs` → file/path helpers

These are exposed as modules, e.g. `math.sqrt(9)`.

## Core builtins

- `show <expr>` prints values
- `ask name = "prompt"` reads text
- `len`, `type`, `num`, `text`

## Collections

- Lists: `push`, `pop`, `insert`, `remove_at`, `copy`, `reverse`, `sort`, `range`
- Higher-order: `map_values(list, fn)`, `filter(list, fn)`, `reduce(list, fn, initial)`
- Maps: `keys`, `values`, `has_key`, `get`, `del_key`
- Sets: `to_set`, `set_has`, `set_add`, `set_remove`

## Text

- `upper`, `lower`, `trim`
- `replace`, `contains`, `starts`, `ends`, `find`, `slice`
- `split`, `join`, `repeat_text`

## Files + paths

- `read_file`, `read_lines`
- `write_file`, `write_lines`, `append_file`
- `exists`, `ls`, `mkdir`
- `cwd`, `path_join`, `basename`, `dirname`

## Math + random + time

- Math: `abs`, `floor`, `ceil`, `round`, `sqrt`, `pow`, `min`, `max`, `clamp`, `sin`, `cos`, `tan`, `log`, `exp`
- Random: `rand`, `randint`, `seed`, `choice`, `shuffle`
- Time: `now_ms`, `sleep_ms`
- Datetime: `now`, `iso`, `parse_time`, `add_ms`, `diff_ms`

## Debug + modules

- `panic(message)` raises a runtime error (useful while debugging)
- `include(path)` executes another file in the current environment

