# ContextVar: Getrennte Rechnung for Parallel Agent Runs

Bob Belderbos recently wrote about [a race condition Rust wouldn't let you write](https://belderbos.dev/blog/race-condition-rust-wouldnt-let-me-write/) — a tool-call counter shared between parallel agents in my multi-agent project. He walked through how Rust's compiler would have blocked the bug at four different points. This is the Python side: how `contextvars.ContextVar` fixed it, and where you'll hit the same pattern in your own multi-agent orchestrators.

## The setup

An orchestrator routes natural-language questions to specialized sub-agents in parallel via `asyncio.gather` — a MongoDB agent for text search and a Cypher agent for graph queries. Each sub-agent should have a budget of five tool calls. Both agents imported the same tracking module:

```python
_call_count = 0
_sources: list[str] = []
_lock = threading.Lock()

def reset() -> None:
    global _call_count, _sources
    with _lock:
        _call_count = 0
        _sources = []

def _check_and_increment() -> int:
    global _call_count
    with _lock:
        if _call_count >= MAX_CALLS:
            raise ToolCallLimitExceeded()
        _call_count += 1
        return _call_count
```

Each agent calls `reset()` at startup and `_check_and_increment()` before each tool call. Both agents share these functions and variables.

In Germany, you can ask for *Getrennte Rechnung* — separate checks. Each person's tab is tracked independently. Elsewhere, restaurants often default to one shared bill for the table. That works fine until you and a friend both agree to cap yourselves at five drinks (which in Berlin counts as showing restraint), but the waiter keeps one shared tally. By your third drink, the count reads five — your friend already ordered two. You stop. You've only had three.

A shared counter when you need separate ones.

## What broke

Python modules are singletons cached in `sys.modules`. `_call_count` is one integer in memory, shared by every execution context. When `asyncio.gather` runs both agents in parallel, they create separate asyncio Tasks — but both Tasks share the same module-level `_call_count`. The result is a **race condition** with two concrete failures:

1. **Shared increments.** Both agents increment the same `_call_count` concurrently, hitting the five-call limit after only 2-3 actual calls each.
2. **Source list leak.** `_sources` accumulates entries from both agents — each agent sees sources from the other's searches.

There's a third failure mode — a later-arriving `reset()` zeroing a running agent's counter — but it requires staggered start times (e.g. a second user's request landing mid-flight). The two above are guaranteed every time `asyncio.gather` runs the agents.

`threading.Lock` made each write atomic — **thread safety** at the operation level, no corrupted increments. It didn't provide **request isolation** — separate state per agent run.

## The race, in one example run

```
Shared counter starts at 0, limit is 5:

MongoDB call 1:  counter 0→1  ✓
Cypher call 1:   counter 1→2  ✓
MongoDB call 2:  counter 2→3  ✓
Cypher call 2:   counter 3→4  ✓
Cypher call 3:   counter 4→5  ✓ (limit reached)
MongoDB call 3:  ✗ BLOCKED

Result: MongoDB made 2/5 calls, Cypher made 3/5 calls
```

Next run: completely different distribution. One agent might complete all 5 calls while the other gets cut off at 1. The orchestrator still returns a response — it just synthesizes from incomplete data, and you can't tell which run produced which quality. Same question, different answer.

## The fix: `contextvars.ContextVar`

A `ContextVar` stores a separate value per execution context. Python creates a fresh context for each OS thread and for each `asyncio.Task`. When an agent reads `_call_count.get()`, it reads its own copy — nothing shared, no lock needed.

```python
import contextvars

_call_count: contextvars.ContextVar[int] = contextvars.ContextVar(
    "call_count", default=0
)
_sources: contextvars.ContextVar[tuple[str, ...]] = contextvars.ContextVar(
    "sources", default=()
)

def reset() -> None:
    _call_count.set(0)
    _sources.set(())

def _check_and_increment() -> int:
    n = _call_count.get()
    if n >= MAX_CALLS:
        raise ToolCallLimitExceeded()
    _call_count.set(n + 1)
    return n + 1

def _add_source(source: str) -> None:
    _sources.set(_sources.get() + (source,))
```

Note the tuple. `ContextVar("sources", default=[])` looks safe but isn't — every context that hasn't called `.set()` shares the same default list object, and a stray `.append()` mutates it for every other context. Same leak in a different form. With a tuple, every update creates a new object via `.set()`, so writes are explicit and contexts stay isolated. Use immutable defaults — `()` or `None`.

After the fix:

```
Each agent has its own counter, isolated via ContextVar:

MongoDB: counter 0→1→2→3→4→5  ✓
Cypher:  counter 0→1→2→3→4→5  ✓
```

*Getrennte Rechnung*: each agent tracks its own count.

## Why not `threading.local`?

`threading.local` gives isolation per OS thread. But all asyncio Tasks run on the same OS thread — `asyncio.gather` creates separate execution contexts (Tasks) without creating separate threads. Two parallel agents within one request still share a `threading.local` value because they share the thread. The race happens within one request via `asyncio.gather`, not just across users.

## Where you might hit this

This bug appears when three conditions meet: module-level per-request state, concurrent execution, and reused agent instances. If you're missing any of these, you won't hit it.

**You're at risk if:**

- **Tool-call budgets** — tracked in module-level counters that reset at request start
- **Source or citation lists** — accumulated at module scope during a run
- **Rate limiting per request** — token counts, API call counters, cost accumulators stored as module variables
- **Orchestrators using `asyncio.gather`** — running sub-agents in parallel on the same shared agent instances
- **Web frameworks** — Streamlit, FastAPI, or Gradio where each session/request runs on its own thread

**You're safe if you avoid module-level state entirely:**

- Pass state explicitly through function parameters or dependency injection
- Store state in request-scoped objects (FastAPI dependencies, Streamlit session_state)
- Use `ContextVar` for shared agent instances that need per-request isolation

Creating new agent instances per request would also work, but initialization is expensive (model loading, connections, prompt compilation). That's why most architectures reuse agent instances — which is exactly when `ContextVar` becomes necessary.

## Why not just use a class?

`ContextVar` fixes the race, but it still relies on module-level declarations. The natural follow-up is: why have module state at all? Why not move the budget into a class?

```python
class ToolCallBudget:
    def __init__(self, max_calls: int = 5):
        self.count = 0
        self.sources: list[str] = []

    def check_and_increment(self) -> int:
        if self.count >= self.max_calls:
            raise ToolCallLimitExceeded()
        self.count += 1
        return self.count
```

That works if you create a new agent per request:

```python
agent = MongoDBSearchAgent(budget=ToolCallBudget())
result = await agent.query(question)
```

But most agent architectures reuse the same agent instance across requests (initialization is expensive). The budget is per-request, not per-agent-instance. You'd need to thread it through every `query()` call and every tool:

```python
async def query(self, question: str, budget: ToolCallBudget):
    await some_tool(question, budget)  # now every tool signature changes
```

If tools access the budget from many places, that's significant refactoring. `ContextVar` is appropriate here because the state is request-scoped but the agent instance is reused. It's not a workaround; it's the right model for implicit per-request context in a shared-instance architecture.

---

Primary sources: [PEP 567](https://peps.python.org/pep-0567/) introduced `contextvars` in Python 3.7. Reference: [docs.python.org/3/library/contextvars](https://docs.python.org/3/library/contextvars.html). Concurrency terminology from Chapter 19 "Concurrency Models in Python" in *Fluent Python* (2nd ed.) by Luciano Ramalho.
