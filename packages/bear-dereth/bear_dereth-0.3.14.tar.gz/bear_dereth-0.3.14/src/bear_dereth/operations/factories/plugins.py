"""Plugin system relating to the tool context factory and dependency injection."""

from __future__ import annotations

from inspect import BoundArguments, Signature
from typing import TYPE_CHECKING, Any, NamedTuple

from bear_dereth.introspection import not_in_bound, type_in_annotation
from bear_dereth.operations.common import PARAM_NAMES, PARAM_OPS, CollectionChoice
from bear_dereth.operations.factories.tool_context import FuncContext, InjectionBase, ToolContext

if TYPE_CHECKING:
    from collections.abc import Callable
    from inspect import BoundArguments, Parameter, Signature

ValidInjectorClasses: tuple[type, ...] = (ToolContext, FuncContext)


class InjectCtx(NamedTuple):
    """Structure to hold injection information."""

    name: str
    call: Callable[..., Any]
    args: list[Any]
    kwargs: dict[str, Any]


# TODO: Should I do this or what? Not sure.
class InjectorManager:
    """Manages a registry of dependency injectors."""

    def __init__(self) -> None:
        """Initialize the injector manager."""
        self._injectors: dict[str, InjectCtx] = {}

    def register(self, name: str, ctx: InjectionBase, injector: Callable) -> None:
        """Register a new injector by name."""
        self._injectors[name] = InjectCtx(name=name, call=injector, args=[ctx], kwargs={})

    def get(self, name: str) -> Any:
        """Retrieve an injector by name."""
        return self._injectors.get(name)


class DependencyInjector:
    """Handles dependency injection for function signatures."""

    def __init__(
        self,
        sig: Signature,
        bound: BoundArguments,
        ctx: ToolContext,
        *,
        choice: CollectionChoice,
        custom: dict[str, InjectCtx] | None = None,
    ) -> None:
        """Initialize the dependency injector with a function signature."""
        self.sig: Signature = sig
        self.bound: BoundArguments = bound
        self.frozen_args: frozenset[str] = frozenset(bound.arguments)  # Freeze for faster lookup
        self.ctx: ToolContext = ctx
        self.choice: CollectionChoice = choice
        self.plugins: dict[str, InjectCtx] = {
            "factory": InjectCtx(name="factory", call=ctx.factory, args=[], kwargs={"choice": choice}),
            **(custom or {}),
        }

    def _param_ops(self, p: str) -> None:
        if p in self.sig.parameters and not_in_bound(self.frozen_args, p):
            self.bound.arguments[p] = getattr(self.ctx, p)

    def _param_names(self, p: str) -> None:
        if p in self.sig.parameters and not_in_bound(self.frozen_args, p):
            self.bound.arguments[p] = self.ctx

    def _sig_params(self, p: Parameter) -> None:
        if type_in_annotation(p, ValidInjectorClasses) and not_in_bound(self.frozen_args, p.name):
            self.bound.arguments[p.name] = self.ctx

    def _inject_plugins(self, ictx: InjectCtx) -> None:
        if ictx.name in self.sig.parameters and not_in_bound(self.frozen_args, ictx.name):
            self.bound.arguments[ictx.name] = ictx.call(*ictx.args, **ictx.kwargs)

    def inject(self) -> BoundArguments:
        """Populate any missing dependency style parameters on the bound arguments."""
        for param in PARAM_OPS:
            self._param_ops(param)
        for param in PARAM_NAMES:
            self._param_names(param)
        for param in self.sig.parameters.values():
            self._sig_params(param)
        for ictx in self.plugins.values():
            self._inject_plugins(ictx)
        self.bound.apply_defaults()
        return self.bound


def inject_dependencies(
    sig: Signature,
    bound: BoundArguments,
    ctx: ToolContext,
    *,
    choice: CollectionChoice,
    custom: dict[str, InjectCtx] | None = None,
) -> BoundArguments:
    """Class method to perform dependency injection."""
    return DependencyInjector(sig, bound, ctx, choice=choice, custom=custom).inject()


def signature_uses_context(sig: Signature) -> bool:
    """Determine whether the callable relies on the ToolContext helpers."""
    any_req_ctx: bool = any(type_in_annotation(param, ValidInjectorClasses) for param in sig.parameters.values())
    return any(name in sig.parameters for name in (*PARAM_NAMES, *PARAM_OPS)) or any_req_ctx
