---
title: "Getting fluent in Python: some notes"
date: 2025-10-01
---

I've decided to dive deep into Python by working through "Fluent Python" by Luciano Ramalho. Here's what I've picked up while doing so.

## Why Fluent Python?
In short, the person I have most learned from on Python recommended it to me. I purchased it, no questions asked.

For the moment, I expect "Fluent Python" to push me to think more in-depth about the language, particularly about the following:
- Python's data model and special methods
- Object-oriented programming patterns
- Functional programming concepts
- Metaprogramming and decorators
- Concurrency and asyncio


## Learning path
### Week 1: The Python Data Model
* The Python Data Model = Python's Internal API
* Special Methods Enable Rich Behavior

## The tip of an iceberg: Python Data Model

Ever wonder why we call `len(collection)`, instead of `collection.len()`? This oddity is the tip of an iceberg: the *Python Data Model*. It defines the **special methods** (often called *dunder methods*, like `__getitem__`, `__len__`, `__repr__`) that classes can implement.

Hence, objects integrate naturally with Python's syntax and built-ins: batteries included 🔋!

- `len(obj)` calls `obj.__len__()`
- `obj[i]` calls `obj.__getitem__(i)`
- `print(obj)` calls `obj.__str__()` or `obj.__repr__()`

## Special Methods

To better appreciate the "batteries included"-aspect of implementing special methods, consider this example of the [zippa](https://pypi.org/project/zippa/) library:

```python
class ZipManager:
    def __init__(self, config: ZipConfig):
        self.config = config
    
    def pack_items(self, items: list[str], output_zip: Path, compress_level: int, 
                   overwrite: bool = False) -> Iterator[str]:
        """Pack items into a zip file with lazy evaluation"""
        yield f"Starting to pack {len(items)} items from current directory"
        
        # Validate output directory
        _validate_output_directory(output_zip)
        
        if output_zip.exists() and not overwrite:
            yield f"Output file {output_zip} already exists. Skipping."
            return
        
        with ZipFile(str(output_zip), "w", ZIP_DEFLATED, compresslevel=compress_level) as archive:
            files_added, dirs_added = 0, 0
            
            for item_str in items:
                if item_str == ".":
                    target_path = Path.cwd()
                else:
                    target_path = Path.cwd() / item_str
                
                # Validate that the item exists
                _validate_item(target_path, item_str)
                yield f"Processing item: {item_str}"
                
                for zip_item in _iter_zip_items(target_path, self.config):
                    if zip_item.item_type == "dir":
                        archive.writestr(zip_item.arcname, "")
                        dirs_added += 1
                        yield f"Added directory: {zip_item.item_path.name}"
                    else:
                        archive.write(zip_item.item_path, arcname=zip_item.arcname)
                        files_added += 1
                        yield f"Added file: {zip_item.item_path.name}"
            
            archive.printdir()
            print(f"Added {files_added} files and {dirs_added} directories to {output_zip}")
            yield f"Completed: {files_added} files, {dirs_added} directories"
    
    # Special Methods from Python Data Model
    
    def __len__(self) -> int:
        """Return number of exclude patterns in config"""
        return len(self.config.exclude_patterns)
    
    def __repr__(self) -> str:
        """Developer representation - unambiguous"""
        return f"ZipManager(config={self.config!r})"
    
    def __str__(self) -> str:
        """User-friendly representation"""
        patterns = ", ".join(self.config.exclude_patterns) if self.config.exclude_patterns else "none"
        return f"ZipManager(exclude_patterns=[{patterns}], include_dirs={self.config.include_dirs})"
    
    def __contains__(self, pattern: str) -> bool:
        """Check if pattern is in exclude patterns"""
        return pattern in self.config.exclude_patterns
    
    def __getitem__(self, index: int) -> str:
        """Get exclude pattern by index"""
        return self.config.exclude_patterns[index]
```

Now we can be super flexible 🕺 with the batteries:

```python
from random import choice

deck = FrenchDeck()
len(deck)  # Works because of __len__

choice(deck)  # Works because of __getitem__

# Slicing works because of __getitem__
deck[:3]

# Iteration works because of __getitem__
for card in deck:
    print(card)

# Reversed iteration works
for reversed_card in reversed(deck):
    print(reversed_card)

# Sorting works
suit_vals = {"spades": 3, "hearts": 2, "diamonds": 1, "clubs": 0}

def spades_high(card: Card) -> int:
    rank_value = FrenchDeck.ranks.index(card.rank)
    return rank_value * len(suit_vals) + suit_vals[card.suit]

for sorted_card in sorted(deck, key=spades_high):
    print(sorted_card)
```

So `__getitem__` enables us to slice, iterate through our instance and sort it! Why? Because when we implement special methods like `__getitem__` and `__len__`, `FrenchDeck` behaves like a standard Python *sequence* 💡!

While `FrenchDeck` implicitly inherits from `object`, **most of its functionality is not inherited**, but comes from leveraging the Data Model as well as from composition.

## How to use Special Methods

Coming back to our initial question of why `len(collection)`, instead of `collection.len()`:

- Special methods **are meant to be called by the Python interpreter, not by you**
- Meaning that if `my_object` is an instance of a user defined class, then `len(my_object)` calls the `__len__` you implemented
- Normally, you should be implementing special methods more often than invoking them explicitly
- If you need to invoke a special method, it's usually better to call the related built-in function (e.g. `len`, `iter`, `str`,...) (the latter call special methods themselves, which is often faster)
- The only exception is `__init__`

## The Most Important Uses of Special Methods

- Emulating Numeric Types
- String Representation
- Boolean Value of a Custom Type

## String Representation: `__repr__` and `__str__`

### `__repr__`

The `__repr__` special method is called by the `repr` built-in to get the string-representation of the object for inspection. If you don't implement it, Python falls back to the default implementation from object, which looks like:

```python
<ClassName object at 0x...>
```

If you do implement it, your objects show meaningful info in:
- The interactive console (REPL, Jupyter, etc.)
- Debugging logs
- Collections (lists, dicts) — because they call `repr` on their elements

Example usage:

```python
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        return f"Card({self.rank!r}, {self.suit!r})"
```

The `!r` in an f-string calls `repr()` on the variable, ensuring the representation is unambiguous (e.g., includes quotes around strings, as in `Vector(1,2)` vs `Vector('1','2')`).

### `__str__`

It's called by `str()` built-in and implicitly used by the `print` function: it **should return a string suitable for display to end users**.

### `__repr__` vs `__str__`

#### Behavior
- `repr(obj)` → calls `obj.__repr__()`
- `str(obj)` → calls `obj.__str__()`, but falls back to `__repr__()` if not implemented
- Interactive consoles (`>>> obj`) and containers (`[obj]`) use `__repr__`

Additional example:

```python
class Card:
    def __init__(self, rank, suit):
        self.rank = rank
        self.suit = suit

    def __repr__(self):
        # Developer-focused: unambiguous, includes quotes
        return f"Card({self.rank!r}, {self.suit!r})"

    def __str__(self):
        # User-focused: friendly, readable
        return f"{self.rank} of {self.suit}"
```

And usage:

```python
c = Card("7", "hearts")

print(repr(c))   # Calls __repr__
# Output: Card('7', 'hearts')

print(str(c))    # Calls __str__
# Output: 7 of hearts

print(c)         # Also calls __str__
# Output: 7 of hearts

cards = [c]
print(cards)     # Uses __repr__ for contained objects
# Output: [Card('7', 'hearts')]
```

#### Best practices
- Always implement `__repr__` in custom classes — it's invaluable for debugging
- Make `__repr__` unambiguous; use `!r` in f-strings for clarity
- Use `__str__` only if you want a different user-facing display. (if not, Python will fall back to `__repr__` automatically)
