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

## Applying Special Methods: A Real Example

To better appreciate the "batteries included"-aspect of implementing special methods, consider this example of the [zippa](https://pypi.org/project/zippa/) library:

```python
class ZipItem(NamedTuple):
    item_type: str
    item_path: Path
    arcname: str

class ZipConfig(NamedTuple):
    exclude_patterns: list[str]
    include_dirs: bool = True

class ZipManager:
    def __init__(self, config: ZipConfig):
        self.config = config

    def pack_items(self, items: list[str], output_zip: Path, compress_level: int,
                   overwrite: bool = False) -> Iterator[str]:
        """Pack items into a zip file with lazy evaluation"""
        yield f"Starting to pack {len(items)} items from current directory"

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

    def __bool__(self) -> bool:
        """Return True if manager has exclude patterns configured"""
        return bool(self.config.exclude_patterns)
```

## The Magic of Special Methods

Now our `ZipManager` integrates naturally with Python's built-ins and we can be super flexible 🕺 with the batteries:

```python
config = ZipConfig(exclude_patterns=['*.pyc', '__pycache__'], include_dirs=True)
manager = ZipManager(config)

# Rich behavior from special methods
print(f"Manager: {manager}")  # Uses __str__
print(f"Debug: {manager!r}")  # Uses __repr__
print(f"Patterns: {len(manager)}")  # Uses __len__
print(f"Excludes pyc: {'*.pyc' in manager}")  # Uses __contains__
print(f"First pattern: {manager[0]}")  # Uses __getitem__
print(f"Has exclusions: {bool(manager)}")  # Uses __bool__

# The actual work with lazy evaluation
for message in manager.pack_items(['src/'], Path('output.zip'), 6):
    print(message)  # Streams results as they're processed
```

## How to use Special Methods

Coming back to our initial question of why `len(collection)`, instead of `collection.len()`:

- Special methods **are meant to be called by the Python interpreter, not by you**
- Meaning that if `my_object` is an instance of a user defined class, then `len(my_object)` calls the `__len__` you implemented
- Normally, you should be implementing special methods more often than invoking them explicitly
- If you need to invoke a special method, it's usually better to call the related built-in function (e.g. `len`, `iter`, `str`,...) (the latter call special methods themselves, which is often faster)
- The only exception is `__init__`

#### Best practices
- Always implement `__repr__` in custom classes — it's invaluable for debugging
- Make `__repr__` unambiguous; use `!r` in f-strings for clarity
- Use `__str__` only if you want a different user-facing display. (if not, Python will fall back to `__repr__` automatically)
