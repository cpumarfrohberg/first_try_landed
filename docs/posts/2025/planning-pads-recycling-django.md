---
title: "Building a Django app for the better good"
date: 2025-11-15
categories:
  - Web Development
---

# Building a Django app for the better good

**Date:** November 11, 2025

I recently built a Django web app to help optimize compost pad layouts for organic waste recycling. The project was inspired by [Wanu Organics](https://www.linkedin.com/company/wanuorganics/posts/?feedView=all), a company working on sustainable waste management solutions.

The app calculates optimal pile configurations for composting facilities—figuring out how many piles fit, their dimensions, and capacity utilization. It's a real-world problem that needed a clean solution.

## Making code maintainable

The biggest win was learning to structure Django apps for maintainability. Instead of cramming everything into views, I organized the code into a **service layer**:

- **OptimizationService** - handles the core business logic
- **DataMapper** - transforms data between web forms and optimization models
- **FormService** - manages form validation and processing
- **SessionService** - handles user session state
- **ErrorHandler** - centralizes error management

This separation made the codebase much easier to test, debug, and extend. When I needed to add a new feature or fix a bug, I knew exactly where to look.

The key lesson: **separate concerns early**. It might feel like over-engineering at first, but it pays off when you need to change things later. Business logic lives in services, not views. Data transformation has its own layer. Each piece has a single responsibility.

## Two code quality wins

### Ternary expressions (Week 8)

Instead of verbose if-else blocks, ternary expressions make conditional assignments concise:

```python
# Before: verbose if-else
if candidate_length > 100:
    adjusted_base = min(pile_base, 100)
else:
    adjusted_base = pile_base

# After: clean ternary
adjusted_base = min(pile_base, 100) if candidate_length > 100 else pile_base
```

### Pydantic models over None checks (Week 4)

Instead of manual `None` validation scattered throughout the code, Pydantic models handle this declaratively:

```python
# Before: manual None checks everywhere
def process_material(method, amount, bulk_density=None):
    if method == "tonnage":
        if bulk_density is None:
            raise ValueError("Bulk density required")
        if bulk_density <= 0:
            raise ValueError("Bulk density must be positive")
    # ... more validation scattered around

# After: Pydantic handles it
class MaterialInput(BaseModel):
    method: InputMeasure
    amount: float = Field(..., gt=0)
    bulk_density: float | None = Field(None, gt=0)

    @field_validator("bulk_density")
    @classmethod
    def validate_bulk_density_required_for_tonnage(
        cls, v: float | None, info: ValidationInfo
    ) -> float | None:
        method = info.data.get("method")
        if method == InputMeasure.TONNAGE and v is None:
            raise ValueError("Bulk density is required when using tonnage method")
        return v
```

Pydantic validates at model creation, so invalid data never enters your business logic.

You can see more of these maintainability patterns in the [project learnings](https://github.com/pybites/PDM_CarlosP/blob/main/wins.md).
