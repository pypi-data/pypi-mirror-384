# DI ↔ ToolContext Integration Sketch

## Why Split Things?
We currently have two injection worlds:
- **`bear_dereth.di`** — declarative container with metaclass magic, lifetime management, and `Provide[...]` markers.
- **Operations Tooling** — lightweight `ToolContext` + decorator that injects context helpers and a tiny plugin dict.

They share ideas (name→provider lookup, lazy resolution) but address different scales. Hardcoding providers in each layer makes it harder to reuse or extend. Extracting reusable pieces from the DI system and firming up the operations plugin API gives us a common language without forcing either layer to swallow the other’s baggage.

## Proposed Separation

### DI Side (long-lived services)
- **Provider Registry**: carve out a small `ProviderRegistry`/`ServiceLocator` object that maps service names (and `Provide` markers) to instances. It should handle overrides and type lookups, but *not* lifecycle.
- **Lifecycle Wrapper**: keep `DeclarativeContainer` focussed on boot/shutdown, teardown queues, and capturing declarative resources. Internally it composes the registry.
- **Public Resolve API**: expose a simple `resolve(name)`/`resolve_marker(provide)` helper that returns instances and can be injected elsewhere without importing metaclass internals.

### Operations Side (per-document tooling)
- **Plugin Registry**: promote the current dict in `DependencyInjector` to a real registry with `register(name, provider)` and (optionally) `register_annotation(cls, provider)` hooks.
- **Decorator Surface**: let `inject_tools` accept a manager (or use a shared default). During binding it asks the registry for providers rather than hardcoding `"factory"`.
- **ToolContext Plugins**: ship built-in plugins for `ctx`, `getter`, `factory`, etc. so user code simply registers additional providers when needed.

## Bridging the Gap
Once both sides speak in terms of providers:
1. **DI-backed plugin**: register a plugin that notices `Provide[...]` defaults or annotations and resolves them via the shared DI registry. Operations that need a “real” service can request it declaratively.
2. **Context-first wiring**: ToolContext plugins keep handling field helpers, collection factories, document state—no dependency on DI unless explicitly requested.

## Rollout Steps
1. Refactor DI internals to extract the provider registry.
2. Introduce the operations plugin manager and migrate the existing `factory` injection to use it.
3. Add a DI plugin that resolves `Provide` markers through the shared registry.
4. Gradually replace ad hoc wiring in operations modules; update tests to cover both context helpers and DI-provided services.

With this split, we keep the functional tooling lean, let heavy services live in the DI layer, and still give operations a straightforward way to ask for them when necessary. Nice modular vibes, no duplicated hardcoding. 🧰✨
