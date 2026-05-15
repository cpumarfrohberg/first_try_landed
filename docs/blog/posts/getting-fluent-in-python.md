---
title: "The Python Data Model: Why len(collection), Not collection.len()"
date: 2026-04-27
categories:
  - Python
tags:
  - python
  - data-model
---

# The Python Data Model: Why `len(collection)`, Not `collection.len()`

**Date:** April 27, 2026

I keep noticing things Python lets me do that I underuse in my own projects. This is the first of a few notes on those — written when the gap shows up in code I'm actually building, not in the abstract.

This one comes from the same multi-agent QA stack as the [structured output post](structured_output_and_contracts.md). The storage layer worked, but felt non-Pythonic. The fix was the data model.

## The tip of an iceberg: Python Data Model

Ever wonder why we call `len(collection)`, instead of `collection.len()`? This oddity is the tip of an iceberg: the *Python Data Model*. It defines the **special methods** (often called *dunder methods*, like `__getitem__`, `__len__`, `__repr__`) that classes can implement.

Hence, objects integrate naturally with Python's syntax and built-ins: batteries included.

- `len(obj)` calls `obj.__len__()`
- `obj[i]` calls `obj.__getitem__(i)`
- `print(obj)` calls `obj.__str__()` or `obj.__repr__()`
- `x in obj` calls `obj.__contains__(x)`
- `for x in obj` calls `obj.__iter__()`

## Where I noticed I was leaving this on the table

I have a `MongoDBStorage` class that wraps a Mongo collection of StackExchange questions:

```python
class MongoDBStorage:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.collection = self.db[MONGODB_COLLECTION]

    def store_questions(self, questions: list[Question]) -> int:
        ...

    def close(self):
        self.client.close()
```

It works. But every time I wanted to ask basic questions about it, I had to leak the MongoDB API:

```python
storage = MongoDBStorage()

storage.collection.count_documents({})              # How many?
storage.collection.find_one({"question_id": 12345}) # Is this one in there?
for doc in storage.collection.find():               # Iterate?
    ...
```

The class wrapped MongoDB, but the *call sites* didn't. To use the wrapper I had to know the thing it was wrapping. That's not encapsulation — that's a leaky abstraction with extra steps.

## The same class, with the data model honored

```python
class MongoDBStorage:
    def __init__(self):
        self.client = MongoClient(MONGODB_URI)
        self.db = self.client[MONGODB_DB]
        self.collection = self.db[MONGODB_COLLECTION]

    def store_questions(self, questions: list[Question]) -> int:
        ...

    def close(self):
        self.client.close()

    def __len__(self) -> int:
        return self.collection.count_documents({})

    def __contains__(self, question_id: int) -> bool:
        return self.collection.find_one({"question_id": question_id}) is not None

    def __iter__(self):
        for doc in self.collection.find():
            yield Question(**doc)

    def __repr__(self) -> str:
        return f"MongoDBStorage(db={self.db.name!r}, collection={self.collection.name!r})"
```

The call sites become Python instead of MongoDB:

```python
storage = MongoDBStorage()

print(f"Stored {len(storage)} questions")           # __len__
if 12345 in storage:                                # __contains__
    print("Already collected")
for question in storage:                            # __iter__
    process(question)
print(repr(storage))                                # __repr__
# MongoDBStorage(db='stackexchange', collection='questions')
```

The wrapper now actually wraps. The MongoDB API stays inside the class.

## Why this matters in a multi-agent project

Multiple agents read from this storage layer. Every place that touched `storage.collection.<something>` was a place where the storage choice (MongoDB vs anything else) bled into the consumer. With the dunder methods, swapping MongoDB for, say, a local cache during tests becomes a one-class change — the agents only know they have something they can `len()`, `in`-check, and iterate over.

That's the contract idea from the [structured output post](structured_output_and_contracts.md), but applied at the object level instead of the data level: the model defines the protocol; the storage just has to fulfill it.

## How to use special methods

Coming back to the initial question — why `len(collection)` instead of `collection.len()`:

- Special methods are meant to be **called by the Python interpreter, not by you**
- If `my_object` is an instance of a user-defined class, then `len(my_object)` calls the `__len__` you implemented
- You should be implementing them more often than invoking them explicitly
- If you do need to invoke one, prefer the related built-in (`len`, `iter`, `str`, ...) — it's clearer and often faster
- The only routine exception is `__init__`

### Best practices

- Always implement `__repr__` in custom classes — it's invaluable for debugging
- Make `__repr__` unambiguous; use `!r` in f-strings for clarity
- Use `__str__` only if you want a different user-facing display (otherwise Python falls back to `__repr__` automatically)
- Don't implement dunders speculatively — add them when a call site reaches *into* your object instead of *talking to* it
