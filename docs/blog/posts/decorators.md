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

A decorator is less like a vitamin and more like the bouncer at any infamous Berlin Club deciding who gets in:
“Single men? No. Mixed-gender groups? Absolutely yes!”

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
And suddenly:
```{Python}
>>> simple("Carlos skates")
'CARLOS SKATES'
```
Same name. Same call. Different behavior.


### What’s Actually Being Intercepted?

When you call:
`simple("Carlos skates")`
three things happen conceptually:

* Python looks up the name simple
* It finds a callable object
* It calls it

A decorator intervenes by changing step 2.

After decoration, simple no longer refers to the original function. It refers to the wrapper. The caller never knows.

That’s interception.

### You Never Reach the Original Directly

After decoration, this is what you really have:

`simple = decorated(simple)`

Call flow:

caller → wrapper → original function (maybe)


The decorator decides:

* whether the original function runs
* when it runs
* with what arguments
* how often
* or not at all

That’s why decorators are used for authentication, caching, logging, retries, validating and rate limiting. They’re gatekeepers.

### The @ Syntax Is Just Sugar
This
```{Python}
@decorated
def simple(name):
    return name
```
Is exactly the same as:
```{Python}
def simple(name):
    return name

simple = decorated(simple)
```
Reassignment is the whole trick:
* Callers don’t call behavior.
* They call names.

To intercept all calls, you must own the name.

A decorator doesn’t enhance a function — it replaces it with a gatekeeper that controls every call that follows.
