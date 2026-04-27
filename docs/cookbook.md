# Cookbook

Small copy/paste recipes.

## Read a file

```veda
make text = read_file("notes.txt")
show len(text)
```

## Write lines

```veda
write_lines("out.txt", ["a", "b", "c"])
```

## Work with lists

```veda
make items = []
push(items, "a")
push(items, "b")
show items

reverse(items)
show items
```

## Filter + map

```veda
work isEven(n) do
    give n % 2 == 0
end

work plusOne(n) do
    give n + 1
end

make nums = [1, 2, 3, 4]
show filter(nums, isEven)
show map_values(nums, plusOne)
```

## Maps (dictionary)

```veda
make m = {"a": 1, "b": 2}
show keys(m)
show values(m)
```

## Random choices

```veda
seed(42)
show randint(1, 6)
show choice(["rock", "paper", "scissors"])
```

## Safe mode

When running scripts you don’t trust, run with safe mode so file access is restricted:

```bash
veda run --safe --allow-root . script.veda
```

