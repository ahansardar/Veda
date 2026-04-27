# Errors (and how to fix them)

Veda errors try to be practical: they show filename, line/column, a caret underline, and an error code.

## Common codes

- `V001` syntax error
- `V101` name error (undefined variable)
- `V201` type error
- `V300` runtime error
- `V401` check error (static check)

## Examples

### Undefined variable (`V101`)

If you see:

- `Undefined variable 'nmae'. Did you mean 'name'?`

Then you probably misspelled the name. Fix the spelling or define it first with `make`.

### Give outside a function (`V300`)

`give` only makes sense inside a `work ... do ... end` function.

### Map keys must be text (`V201`)

Maps use text keys: `{"a": 1}` and you access them via `m["a"]`.

## Tips

- Run `veda check file.veda` before `veda run ...`
- In the REPL, use `:check` to check the last input

