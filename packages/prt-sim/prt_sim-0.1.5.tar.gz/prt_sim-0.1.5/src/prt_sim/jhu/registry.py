from __future__ import annotations
from dataclasses import dataclass
from importlib import import_module
from importlib.metadata import entry_points
from typing import Any, Callable, Dict, Optional

# In-memory registry (runtime registration support)
_REGISTRY: Dict[str, str] = {}
_DISCOVERED: bool = False

@dataclass(frozen=True)
class Spec:
    id: str
    entry_point: str  # "pkg.module:callable"

def _discover_entry_points(group: str = "jhu.envs") -> None:
    """Load installed entry points one time into _REGISTRY."""
    global _DISCOVERED
    if _DISCOVERED:
        return
    eps = entry_points()
    group_eps = eps.select(group=group) if hasattr(eps, "select") else eps.get(group, [])
    for ep in group_eps:
        # ep.name is the ID, ep.value is "module:attr" (older pkg resources) OR
        # ep.module + ep.attr if using new API. Handle both:
        try:
            value = getattr(ep, "value", None) or f"{ep.module}:{ep.attr}"
        except Exception:
            # Fallback to 'value' for older metadata
            value = ep.value  # type: ignore[attr-defined]
        if ep.name not in _REGISTRY:  # don't clobber runtime registrations
            _REGISTRY[ep.name] = value
    _DISCOVERED = True

def register(id: str, entry_point: str) -> None:
    """
    Register at runtime (e.g., in tests or plugins):
    register("JHU/MyEnv-v0", "my_pkg.my_mod:MyEnvClass")
    """
    _REGISTRY[id] = entry_point

def _load_callable(spec: str) -> Callable[..., Any]:
    """
    Import and return the callable referenced by "module:attr".
    """
    if ":" not in spec:
        raise ValueError(f"Entry point must be 'module:attr', got: {spec!r}")
    module_name, attr = spec.split(":", 1)
    mod = import_module(module_name)
    try:
        fn = getattr(mod, attr)
    except AttributeError:
        raise ImportError(f"Cannot find attribute {attr!r} in module {module_name!r}")
    if not callable(fn):
        raise TypeError(f"Entry point target must be callable, got: {type(fn)} from {spec}")
    return fn

def make(id: str, /, **kwargs: Any) -> Any:
    """
    Create an instance by string ID. Works with classes or factory functions.
    Example: env = jhu.make("JHU/ImagePipeline-v0", width=64, height=64)
    """
    _discover_entry_points()
    spec = _REGISTRY.get(id)
    if spec is None:
        # Helpful diagnostics
        available = ", ".join(sorted(_REGISTRY.keys())) or "<none>"
        raise KeyError(f"Unknown JHU id {id!r}. Available: {available}")
    ctor = _load_callable(spec)
    return ctor(**kwargs)

def specs(prefix: Optional[str] = None) -> Dict[str, Spec]:
    """List all registered specs, optionally filtered by ID prefix."""
    _discover_entry_points()
    out = {}
    for k, v in _REGISTRY.items():
        if prefix is None or k.startswith(prefix):
            out[k] = Spec(id=k, entry_point=v)
    return out
