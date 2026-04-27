# Veda tour (10 minutes)

Veda is a beginner-friendly scripting language with a clean “read it out loud” syntax.

## Hello

```veda
show "Namaste from Veda"
```

## Variables + math

```veda
make a = 10
make b = 20
show a + b
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

## Loops + control

```veda
count i from 1 to 10 do
    next when i == 2
    stop when i == 5
    show i
end
```

## Lists + maps

```veda
make a = [1, 2, 3]
show a[1:]        # [2, 3]
a[0] = 99
show a

make m = {"name": "Ahan"}
show m["name"]
m["name"] = "Veda"
show m["name"]
```

## Functions

```veda
work add(a, b) do
    give a + b
end

show add(10, 20)
```

## Modules

Built-in modules:

```veda
use math
show math.sqrt(9)
```

File modules:

```veda
use "lib.veda"
show lib.someFunction(1)
```

