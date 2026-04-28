---
title: "Structured Output: Passport Control at Departure, Not Customs at Arrival"
date: 2026-04-22
categories:
  - Python
tags:
  - python
  - pydantic
  - architecture
  - ai-agents
---

# Structured Output: Passport Control at Departure, Not Customs at Arrival

**Date:** April 22, 2026

Bob Belderbos wrote a [sharp breakdown](https://belderbos.dev/blog/ai-agent-architecture-python/) of AI agent architecture.
Layer 2 makes the key move: return a Pydantic model, not a string.

```python
class ExpenseCategorizationResponse(BaseModel):
    category: str
    total_amount: Decimal
    currency: Currency
    confidence: float
    cost: Decimal
    comments: str | None = None
```

No regex. No JSON parsing. No `float(response.split("$")[1])` hacks.
This post shows what that looks like in a multi-agent setup — and where the idea goes next.

### Consider a Multi-Agent Setup

Imagine a system that answers natural language questions about developer behavior on StackExchange.
Questions arrive at an orchestrator, which routes them to one of two sub-agents — or both in parallel:

- **MongoDB/RAG agent** — text search over StackExchange documents
- **Neo4j/Cypher agent** — graph traversal over a knowledge graph built from the same data

A judge model then scores each answer for accuracy, completeness, and relevance.
Three agents, one pipeline, zero shared state except typed contracts.

Like an airport: a dispatcher routes each flight to the right terminal — domestic, international, or both when the itinerary requires a connection. A quality inspector reviews every landing report.

### What's Really Happening

The schema travels with the request.
The model is constrained at generation time — you receive typed data, not text you then try to shape into it.

Like an airport: passport control checks departures, but without customs, arrivals are unregulated. Structured output is that missing arrivals gate — the model can't hand you a bag that doesn't match the declared contents.

### Three Agents, Same Contract

Every agent declares its output type — structured output is not an option, it's the architecture:

```python
Agent(name="orchestrator_agent", ..., output_type=OrchestratorAnswer)
Agent(name="mongodb_agent",      ..., output_type=SearchAnswer)
Agent(name="judge",              ..., output_type=JudgeEvaluation)
```

Even the evaluator is constrained. The judge can't hand back a paragraph of opinions.
It must produce `accuracy`, `completeness`, and `relevance` as floats, or it doesn't clear customs.

Every agent declares the same kind of contract. It doesn't matter whether it's the orchestrator, a sub-agent, or the judge — the reader expects the same structure.

### Nesting the Decision Inside the Response

`OrchestratorAnswer` nests a routing log inside the response itself:

```python
class RoutingLog(BaseModel):
    route: Literal["RAG", "CYPHER", "BOTH"]
    tool_called: Literal[
        "call_mongodb_agent",
        "call_cypher_query_agent",
        "call_both_agents_parallel",
    ]
    reason: str  # one-line rationale, ≤ 12 words
    queries: dict[str, str]  # reformulated queries per sub-agent, e.g. {"rag": "...", "cypher": "..."}
    notes: str
```

`route: Literal["RAG", "CYPHER", "BOTH"]` is not a label you validate after the fact.
It's a three-option constraint sent to the model at generation time.

The model cannot route to a fourth destination that doesn't exist.
The routing decision itself is a contract — and the trail is in the document, not in someone's memory.

### The Service Layer Inherits the Guarantee

Once the orchestrator returns, the code is unconditional:

```python
result = await self.agent.run(question)

logger.info(f"Route: {result.output.routing_log.route}")
print(f"✅ Used agents: {', '.join(result.output.agents_used)}")
```

No `if result.output.routing_log is None`. No `try/except` around `.route`.

The contract was enforced at the source. The service layer inherits it.

Like an airport: once you've cleared security, the departure lounge doesn't ask for your passport again. The upstream checkpoint already did the work.

### The Weakest Link

Both sub-agents have the same gap:

```python
class SearchAgentResult(BaseModel):
    answer: SearchAnswer
    tool_calls: list[dict]  # ← untyped
    token_usage: TokenUsage
```

`list[dict]` is customs with no scanner. A `ToolCall` model closes it:

```python
class ToolCall(BaseModel):
    name: str
    arguments: dict[str, Any]
    result: str | None = None

class SearchAgentResult(BaseModel):
    answer: SearchAnswer
    tool_calls: list[ToolCall]  # ← typed end to end
    token_usage: TokenUsage
```

The contract is only as strong as its weakest field — one untyped `list[dict]` is the unchecked bag.

### What Structured Output Does Not Fix

Customs checks the form of the declaration. Not whether it's honest.

`Literal["RAG", "CYPHER", "BOTH"]` guarantees the model picks one of three valid routes.
It does not guarantee it picks the *right* one. The LLM weighs the instructions and
interprets the question — it does not execute a switch statement.

`RoutingLog` is also retrospective: it records what happened after the tool was called,
not a decision that drove it. The structure is auditable. The choice is still probabilistic.

What closes that gap: routing ground truth, regression tests before any prompt change,
and a `route` column in monitoring so you can see drift before answer quality tells you about it.

Structured output is necessary. It is not sufficient.

Like an airport: a valid boarding pass proves your seat exists. It doesn't prove the pilot will land on time.
