# Veda v1.0

Veda is a small, beginner-friendly interpreted programming language with its own `.veda` file extension and a readable “teach it on a whiteboard” syntax.

Veda is **not** Python syntax — Python is only used to implement the first bootstrap interpreter (Stage 0).


## What you can do

- Run a `.veda` file: `veda run examples/hello.veda`
- Check syntax: `veda check examples/functions.veda`
- Use the REPL: `veda repl`

## Quick start (no install)

```bash
python main.py run examples/hello.veda
python main.py run examples/functions.veda
python main.py repl
```

## Install the `veda` CLI (recommended)

```bash
pip install -e .
```

Then:

```bash
veda run examples/hello.veda
```

## Veda syntax (tiny tour)

```veda
make name = "Ahan"
make age = 18

show "Name: " + name
show age + 10

when age >= 18 do
    show "Adult"
else do
    show "Minor"
end

work add(a, b) do
    give a + b
end

show add(10, 20)
```

More: `docs/syntax.md`

## Repo layout

```
veda/veda/     # interpreter package
examples/      # sample .veda programs
tests/         # pytest tests
docs/          # short docs for collaborators
main.py        # convenience entrypoint
```

## Roadmap

See `docs/roadmap.md`.

## Testing

```bash
pytest
```
