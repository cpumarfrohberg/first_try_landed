---
title: "What I learned about decorators"
date: 2026-02-01
categories:
  - Python
---

# Decorators Are Not Enhancements — They’re Interceptions

**Date:** February 01, 2026

I’ve been thinking about decorators and realized my original simile — decorators as sharks eating smaller fish — was… limited. The usual claim that decorators “enhance” functions never really worked for me either. Meh.

Yes, decorators technically work like this:
`decorated = decorator(fn)`,
But that description misses the point. Decorators don’t enhance functions. They intercept function calls.

A decorator is less like a vitamin and more like the bouncer at Berlin’s KitKatClub deciding who gets in:
“Single men? No. Groups? Hell yes.”

Same door. Same people. Different outcome.

### A Minimal Example



Think of a simple function returning a string as in
```{Python}
def simple(name: str) -> str:
    return name
```
```
>>> simple("Carlos skates")
'Carlos skates'
```
Now the decorator:
```{Python}
def decorated(fn):
    def wrapper(name: str):
        return fn(name.upper())
    return wrapper
```
