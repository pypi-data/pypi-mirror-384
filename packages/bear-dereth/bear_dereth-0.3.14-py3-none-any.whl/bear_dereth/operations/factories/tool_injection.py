"""Tool injection decorator and helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bear_dereth.introspection import get_function_signature
from bear_dereth.operations.factories.plugins import ToolContext, inject_dependencies, signature_uses_context

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import BoundArguments, Signature

    from bear_dereth.operations.common import CollectionChoice, Item, Params, Return


def inject_tools(
    op_func: Callable[Params, Return] | None = None,
    *,
    default_factory: CollectionChoice = "dict",
) -> Callable[..., Any]:
    """Decorator that injects ToolContext helpers and collection factories.

    Works in two modes:

    1. If the target function references context helpers (e.g. ``ctx`` or
       ``getter``), a partially applied callable is returned, mirroring
       ``inject_ops`` behaviour.
    2. Otherwise the wrapper behaves like ` `Inject.factory`` and executes the
       function immediately after injecting ``factory`` when necessary.
    """

    def decorator(func: Callable[Params, Return]) -> Callable[..., Any]:
        sig: Signature = get_function_signature(func)
        requires_context: bool = signature_uses_context(sig)
        expects_factory: bool = "factory" in sig.parameters

        def _prepare_bound(ctx: ToolContext[Any], *args: Params.args, **kwargs: Params.kwargs) -> BoundArguments:
            bound: BoundArguments = sig.bind_partial(*args, **kwargs)
            return inject_dependencies(sig, bound, ctx, choice=default_factory)

        if requires_context:

            def op_factory(*args: Params.args, **kwargs: Params.kwargs) -> Callable[[Item], Return]:  # type: ignore[override]
                base_args = args
                base_kwargs = kwargs

                def transform(doc: Item) -> Return:
                    ctx: ToolContext[Item] = ToolContext.get_singleton()
                    ctx.set_default_choice(default_factory)
                    ctx.update(doc)
                    bound: BoundArguments = _prepare_bound(ctx, *base_args, **base_kwargs)
                    return func(*bound.args, **bound.kwargs)

                return transform

            return op_factory

        def wrapper(*args: Params.args, **kwargs: Params.kwargs) -> Return:
            ctx: ToolContext[Any] = ToolContext.get_singleton()
            ctx.set_default_choice(default_factory)
            bound: BoundArguments = sig.bind_partial(*args, **kwargs)
            if expects_factory and "factory" not in bound.arguments:
                bound.arguments["factory"] = ctx.factory(choice=default_factory)
            bound.apply_defaults()
            return func(*bound.args, **bound.kwargs)

        return wrapper

    if op_func is not None:
        return decorator(op_func)
    return decorator


inject_ops = inject_tools  # Backwards compatibility alias for experimentation.

if __name__ == "__main__":
    # ruff: noqa: S101, D103

    @inject_tools
    def upper(field: str, ctx: ToolContext) -> None:
        value: Any = ctx.getter(field)
        if isinstance(value, str):
            ctx.setter(field, value.upper())

    @inject_tools
    def merge_dicts(*dicts: dict[str, Any], factory: Callable[..., dict[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = factory()
        for d in dicts:
            result.update(d)
        return result

    doc: dict[str, Any] = {"name": "bear", "age": 42}
    upper_name: Any = upper("name")
    upper_name(doc)
    assert doc["name"] == "BEAR"

    merged = merge_dicts({"a": 1}, {"b": 2})
    assert merged == {"a": 1, "b": 2}

    def ordered_dict_factory() -> dict[str, Any]:
        return {"_ordered": True}

    merged_custom = merge_dicts({"x": 1}, factory=ordered_dict_factory)
    assert merged_custom["_ordered"] is True
