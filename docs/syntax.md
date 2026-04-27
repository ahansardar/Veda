# Veda v1.0 Syntax (practical guide)



## Values and types

Veda has these runtime types:

- `number` (integers + decimals)
- `text` (double-quoted strings)
- `bool` (`true` / `false`)
- `none` (returned by functions that don’t `give`)
- `function` (built-ins and `work` functions)

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

- `len(text)` → number (length of a text value)
- `type(value)` → text (`number`, `text`, `bool`, `none`, `function`)
- `num(value)` → number (converts text like `"123"` or `"3.14"`)
- `text(value)` → text
- `upper(text)` → text
- `lower(text)` → text
- `trim(text)` → text
- `abs(number)` → number
- `floor(number)` → number
- `ceil(number)` → number
- `round(number)` → number

## Comments

```veda
# This is a comment
```
