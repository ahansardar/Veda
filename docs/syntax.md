# Veda v1.0 Syntax (practical guide)



## Values and types

Veda has these runtime types:

- `number` (integers + decimals)
- `text` (double-quoted strings)
- `bool` (`true` / `false`)
- `list` (ordered collection)
- `map` (key/value dictionary; keys are text)
- `set` (unique collection)
- `bytes` (raw bytes)
- `datetime` (date/time value)
- `none` (returned by functions that don’t `give`)
- `function` (built-ins and `work` functions)
  - plus `module` values from `use`

You can ask for a type:

```veda
show type(10)       # number
show type("hello")  # text
show type(true)     # bool
```

## Variables

Declare variables with `make`:

```veda
make name = "Ahan"
make age = 18
make pi = 3.14
make isStudent = true
```

Reassign without `make`:

```veda
make x = 10
x = 20
show x
```

## Output

```veda
show "Hello World"
show "Hello " + "Veda"
show 10 + 5
```

`+` concatenates when either side is text:

```veda
show "Age: " + 18
```

## Text interpolation (v1.0)

Text values can embed variables using `{name}`:

```veda
make name = "Ahan"
show "Hello {name}"
```

To write literal braces, use `{{` and `}}`:

```veda
show "{{ok}}"
```

Multi-line text is supported with triple quotes:

```veda
show """Line 1
Line 2"""
```

## Input

`ask` reads text from the user:

```veda
ask name = "Enter your name: "
show "Hello " + name
```

## Conditions

```veda
make marks = 92

when marks >= 90 do
    show "Excellent"
else do
    show "Keep improving"
end
```

## Loops

Repeat N times:

```veda
repeat 3 times do
    show "Veda is running"
end
```

Count in an inclusive range:

```veda
count i from 1 to 5 do
    show i
end
```

Iterate over a list, text, or map keys:

```veda
each item in [1, 2, 3] do
    show item
end
```

You can also use two loop variables:

- For lists/text: `each index, item in items do ... end`
- For maps: `each key, value in m do ... end`

Loop control:

```veda
count i from 1 to 10 do
    next when i == 2
    stop when i == 5
    show i
end
```

## Functions

Define with `work`, return with `give`:

```veda
work add(a, b) do
    give a + b
end

show add(10, 20)
```

## Operators (v1.0)

- Arithmetic: `+ - * / %`
- Comparison: `== != > < >= <=`
- Logical: `and or not`

Truthiness rules:

- `false`, `0`, `""`, and `none` are false
- everything else is true

## Built-in functions (v1.0)

- Core:
  - `len(text|list)` → number
  - `type(value)` → text (`number`, `text`, `bool`, `list`, `map`, `none`, `function`)
  - `num(value)` → number
  - `text(value)` → text

- Text:
  - `upper`, `lower`, `trim`
  - `replace(text, old, new)` → text
  - `contains/starts/ends` → bool
  - `find(text, part)` → number (index, or `-1`)
  - `slice(text, start, end)` → text
  - `split(text, sep)` → list
  - `join(list, sep)` → text
  - `repeat_text(text, times)` → text

- Lists:
  - `push/pop/insert/remove_at` (mutating)
  - `copy(list)` → list
  - `reverse(list)` → none (mutates)
  - `sort(list)` → none (mutates; sorts by text form)
  - `range(start, end)` → list (inclusive)

- Maps:
  - `keys(map)` → list
  - `values(map)` → list
  - `has_key(map, key)` → bool
  - `get(map, key[, default])` → value
  - `del_key(map, key)` → value

- Math:
  - `abs/floor/ceil/round`
  - `sqrt`, `pow`, `min`, `max`, `clamp`
  - `sin`, `cos`, `tan`, `log`, `exp`

- Random + time:
  - `rand()`, `randint(lo, hi)`, `seed(n)`
  - `choice(list)`, `shuffle(list)`
  - `now_ms()`, `sleep_ms(ms)`

- Files + paths:
  - `read_file`, `read_lines`
  - `write_file`, `write_lines`, `append_file`
  - `exists`, `ls`, `mkdir`
  - `cwd`, `path_join`, `basename`, `dirname`

- Debug:
  - `panic(message)` → raises a runtime error

- Types:
  - `bytes(text)` → bytes
  - `from_hex(text)` → bytes
  - `to_hex(bytes)` → text
  - `utf8(bytes)` → text
  - `now()` → datetime
  - `iso(datetime)` → text
  - `parse_time(text)` → datetime
  - `add_ms(datetime, ms)` → datetime
  - `diff_ms(a, b)` → number
  - `to_set(list)` → set
  - `set_has(set, value)` → bool
  - `set_add(set, value)` → none
  - `set_remove(set, value)` → none

Constants:

- `pi`
- `e`

## Lists (v1.0)

Create a list with square brackets:

```veda
make a = [1, 2, 3]
show a
```

Indexing works on lists and text:

```veda
show a[0]
show "hello"[1]   # "e"
```

Slicing works on lists and text:

```veda
show a[1:]     # [2, 3]
show a[:2]     # [1, 2]
show a[1:2]    # [2]
```

Index assignment (lists only):

```veda
a[0] = 99
```

Mutating helpers:

```veda
make items = []
push(items, "a")
push(items, "b")
show items
show pop(items)
show items
```

## Maps (v1.0)

Maps use `{ key: value }` and keys must be text:

```veda
make m = {"name": "Ahan", "age": 18}
show m["name"]
```

You can also assign into a map:

```veda
m["age"] = 19
```

## Modules (v1.0)

Use `use` to execute a file **once** (cached by absolute path):

```veda
use "lib.veda"
```

Or load a built-in stdlib module:

```veda
use math
show math.sqrt(9)
```

Export control (in module files):

```veda
make secret = 1
make public = 2
share public
```

If you want to run a file every time, use:

```veda
include("lib.veda")
```

## Program arguments

When you run a file as `veda run myfile.veda one two`, the extra words are available as:

```veda
show args
```

## Comments

```veda
# This is a comment
```
