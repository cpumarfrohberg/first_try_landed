---
title: "Decorators: The Bouncer Owns the Door, Not You"
date: 2026-02-01
categories:
  - Python
tags:
  - python
  - decorators
  - function-design
---

# Decorators: The Bouncer Owns the Door, Not You

**Date:** February 01, 2026

The usual description of decorators — that they "enhance" or "wrap" a function — never really clicked for me. It describes the mechanism but misses the point.

Yes, decorators technically work like this: `decorated = decorator(fn)`. But that's the how, not the what. What a decorator actually does is intercept every call to a function.

Think of the bouncer at any infamous Berlin club:
"Single men? No. Mixed-gender groups? Absolutely yes!"

Same door. Same people. Different outcome — because somebody else now decides what the door means.

### A Minimal Example

Think of a simple function returning a string:

```python
def simple(name: str) -> str:
    return name
```

```python
>>> simple("Carlos skates")
'Carlos skates'
```

Now the decorator:

```python
def decorated(fn):
    def wrapper(name: str):
        return fn(name.upper())
    return wrapper
```

And suddenly:

```python
>>> simple("Carlos skates")
'CARLOS SKATES'
```

Same name. Same call. Different behavior.

Like the Berlin club: same entrance, same guest — but the bouncer changed what went through.

### What's Actually Being Intercepted?

When you call `simple("Carlos skates")`, three things happen conceptually:

- Python looks up the name `simple`
- It finds a callable object
- It calls it

A decorator intervenes by changing step 2.

After decoration, `simple` no longer refers to the original function. It refers to the wrapper. The caller never knows.

Like the club: the guest doesn't negotiate with the original door policy. They negotiate with whoever is standing in front of it. The bouncer is now the policy.

That's interception.

### You Never Reach the Original Directly

After decoration, this is what you really have:

```python
simple = decorated(simple)
```

Call flow:

```
caller → wrapper → original function (maybe)
```

The decorator decides:

- whether the original function runs
- when it runs
- with what arguments
- how often
- or not at all

Like the bouncer: the original door still exists. But nobody gets to it without the bouncer's say-so. The original function didn't change — access to it did.

### The @ Syntax Is Just Sugar

This:

```python
@decorated
def simple(name):
    return name
```

Is exactly the same as:

```python
def simple(name):
    return name

simple = decorated(simple)
```

Reassignment is the whole trick. Callers don't call behavior — they call names. To intercept all calls, you must own the name.

Like the club: `@decorated` is just posting the bouncer at the door before opening night. The result is identical — guests will never know there was ever a different arrangement.

### What this requires from the language

`simple = decorated(simple)` works because Python names are runtime bindings. Any code, at any point during execution, can rebind a name to a different object. The original function still exists in memory — it's just unreachable by that name.

In Rust this is impossible. Function bindings are resolved at compile time. The compiler owns the name; no code can swap it out at runtime.

Rust has something that looks similar: procedural macros like `#[tokio::main]` or `#[test]`. A marker on a function that changes its behavior — same syntax energy as `@decorator`. But the mechanism is completely different. Macros transform source code at compile time, before anything runs. There is no wrapper, no name swap, no bouncer posted at a door that already exists. The door is redesigned before the building opens.

Python's decorator works because Python lets you own the name at runtime. That's the feature.

### Why This Matters

That's why decorators are used for authentication, caching, logging, retries, and rate limiting.

- **Authentication**: the bouncer checks your ID before you enter
- **Caching**: the bouncer recognizes you from last time and waves you through without the full check
- **Logging**: the bouncer keeps a clipboard — every entry and exit timestamped
- **Retries**: the bouncer sends you to the back of the queue and lets you try again
- **Rate limiting**: the bouncer has a counter — after ten entries, the door closes for an hour

Same door. The bouncer just decides what the door means.

### In a multi-agent system

The five use cases above all appear in the multi-agent system from the [structured output post](structured_output_and_contracts.md). Here are three of them.

**Caching**: `_get_orchestrator_agent` builds the entire agent stack — database connections, model config, tool registration. Called on every Streamlit rerun without the decorator, it would rebuild from scratch every few seconds. `@st.cache_resource` owns that decision now. The function may not run at all.

```python
@st.cache_resource
def _get_orchestrator_agent() -> OrchestratorAgent:
    ...
```

Like the bouncer: recognizes you from last time, waves you through. The original function is still there. You just don't reach it.

**Retries**: `load_stackexchange_graph_from_mongodb` has no knowledge of failure or recovery. `@retry(tries=100, delay=10)` owns that entirely — it decides whether the function runs again, how many times, and with what delay between attempts.

```python
@retry(tries=100, delay=10)
def load_stackexchange_graph_from_mongodb(...):
    ...
```

Like the bouncer: sends you to the back of the queue and lets you try again. Up to 100 times.

**Registration**: `collect`, `agent_ask`, and the other CLI commands in `cli.py` are never called directly. `@app.command()` registers each one as a Typer subcommand. When a user runs `python cli.py collect`, Typer's wrapper parses `sys.argv`, validates inputs, and decides what reaches the original function.

```python
@app.command()
def collect(...):
    ...
```

Like the bouncer: you negotiate with whoever is standing at the door. The original function didn't change — access to it did.

A decorator doesn't enhance a function — it replaces it with a gatekeeper that controls every call that follows.
