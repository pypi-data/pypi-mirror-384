# Functional Factory Unification (Thought Sketch)

## Goals
- Reuse one injection story for both stateful field operations (`operationstuffs.py`) and pure constructors (`dictstuffs.py`).
- Let callers override the collection factory while keeping a safe default.
- Keep the “functional tools” experience: partially apply once, then call with a doc or data payload.

## Core Concept — `ToolContext`
- Promote `FuncContext` into a richer `ToolContext`.
- Store the active document plus a lazily-evaluated `factory_choice` (`dict`, `list`, etc.).
- Allow overrides via `ToolContext.with_factory(...)` so composed functions can slot in custom factories.
- Provide helper accessors (`ctx.getter`, `ctx.factory()`, etc.) to hide the wiring.

```python
class ToolContext(Generic[T]):
    def __init__(self, doc: T | None = None, *, choice: CollectionChoice = "dict") -> None:
        self.doc = doc
        self._choice = choice
        self._factory_override: Callable[..., Any] | None = None

    def update(self, doc: T, *, choice: CollectionChoice | None = None) -> None:
        self.doc = doc
        if choice is not None:
            self._choice = choice

    def with_factory(self, factory: Callable[..., Any]) -> ToolContext[T]:
        clone = copy.copy(self)
        clone._factory_override = factory
        return clone

    def factory(self, *, choice: CollectionChoice | None = None) -> Callable[..., Any]:
        if self._factory_override:
            return self._factory_override
        return default_factory(choice=choice or self._choice)
```

## Injector Strategy
1. Resolve the target function signature once during decoration.
2. Build a `providers` mapping:
   - `FuncContext`, `ToolContext`, `ctx`, `container` ⇒ the shared context.
   - `getter`, `setter`, `deleter` ⇒ bound methods from the context.
   - `factory` ⇒ `context.factory(...)`, honoring caller overrides.
3. At call time:
   - Create/obtain a singleton `ToolContext`.
   - Update it with the incoming document (if present).
   - Bind positional/keyword args.
   - Fill any missing parameters from the provider map.
   - Rebind `factory` if a user supplied a `factory=` kwarg when creating the operation (`inject.with_factory(...)` case).

```python
def inject_tools(op: Callable[P, Return]) -> Callable[..., Callable[..., Return]]:
    sig = get_function_signature(op)
    needs_factory = "factory" in sig.parameters

    def op_factory(*args, factory: Callable[..., Any] | None = None, **kwargs):
        ctx = ToolContext.get_singleton()
        if factory:
            ctx = ctx.with_factory(factory)
        bound = sig.bind_partial(*args, **kwargs)

        for name, provider in providers.items():
            if name in sig.parameters and name not in bound.arguments:
                bound.arguments[name] = provider(ctx)

        def call(doc):
            ctx.update(doc)
            bound.arguments.setdefault("factory", ctx.factory())
            return op(**bound.arguments)

        return call

    return op_factory
```

## Usage Examples

### Mutating Operations
```python
@inject_tools
def upper(field: str, ctx: ToolContext) -> None:
    value = ctx.getter(field)
    if isinstance(value, str):
        ctx.setter(field, value.upper())
```

*Call site:* `upper_name = upper("name")`; `upper_name(doc)` — the injector fills in the context and helpers.

### Pure Constructors
```python
@inject_tools
def merge_dicts(*dicts: dict[str, Any], factory: Callable[..., dict[str, Any]]) -> dict[str, Any]:
    result = factory()
    for d in dicts:
        result.update(d)
    return result
```

*Call site:* `merge = merge_dicts(factory=my_custom_factory)` or `merge = merge_dicts()`; the returned callable still accepts documents/data as needed.

## Migration Steps
1. Implement `ToolContext` (backward-compat: alias `FuncContext = ToolContext` for now).
2. Replace `inject_ops`, `Factory.inject`, and `Inject.factory` with the unified `inject_tools`.
3. Update existing operations (`operationstuffs.py`, `dictstuffs.py`, etc.) to request the parameters they need.
4. Adjust tests to cover both default factory behaviour and custom overrides.
5. Once stable, delete old injectors and tidy up imports.

This keeps the current ergonomics but gives you a single place to enrich the “functional toolbox” as you add more capabilities (e.g., transaction helpers, logging hooks, async adapters). 🧰✨
