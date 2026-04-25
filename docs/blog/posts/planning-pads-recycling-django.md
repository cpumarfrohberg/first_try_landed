---
title: "Building a Django app for the better good"
date: 2025-11-15
categories:
  - Web Development
tags:
  - django
  - architecture
  - pydantic
  - maintainability
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

### Models vs optimization: knowing where logic belongs

A key insight was understanding the distinction between `models.py` and `optimize.py`:

- **`models.py`**: Defines what valid data looks like (Pydantic models, validation rules, basic calculations). It's the blueprint.
- **`optimize.py`**: Contains the optimization algorithm that arranges those valid piles efficiently. It's the architect.

Think of it this way: `models.py` defines what a valid pile is, `optimize.py` figures out how to arrange them optimally. This separation keeps data validation separate from algorithmic logic, making both easier to test and modify.

## Two code quality wins while working on the project

### Ternary expressions

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

### Pydantic models over None checks

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

### Field constraints vs custom validators

Pydantic offers two approaches for validation. Use `Field` constraints for simple checks:

```python
# Simple constraint - concise and clear
height: float = Field(..., gt=0, description="Must be positive")
```

Use `@field_validator` when you need custom logic or error messages:

```python
# Custom validator - handles complex scenarios
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

**Rule of thumb**: Use `Field` constraints for simple validations (gt, lt, min_length, etc.). Use custom validators when you need conditional logic or specific error messages.

### Django vs Pydantic: choosing the right validation

For a Django project, Django's built-in validation is usually the better choice:

- **Django forms** integrate seamlessly with templates and CSRF protection
- **Django models** have validation tied to database operations
- **Less complexity** - no extra validation layer needed

Pydantic shines in API contexts (like FastAPI) where you need automatic OpenAPI documentation and serialization. But for traditional Django web apps, Django's validation system is more appropriate and better integrated.

I used Pydantic in this project because the optimization logic needed to work independently of Django (could be used as a CLI tool), but for pure Django web apps, stick with Django's validation.
