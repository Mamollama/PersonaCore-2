"""Generator registry — maps backend IDs to generator classes."""

from __future__ import annotations

from typing import Type

from personacore.logging_module import get_logger
from .base_generator import BaseVideoGenerator

log = get_logger("video.registry")


class GeneratorRegistry:
    """Central registry for video generator backends."""

    def __init__(self) -> None:
        self._backends: dict[str, Type[BaseVideoGenerator]] = {}

    def register(self, backend_id: str, cls: Type[BaseVideoGenerator]) -> None:
        self._backends[backend_id] = cls
        log.debug("Registered video backend: %s -> %s", backend_id, cls.__name__)

    def get(self, backend_id: str) -> Type[BaseVideoGenerator] | None:
        return self._backends.get(backend_id)

    def create(self, backend_id: str) -> BaseVideoGenerator | None:
        cls = self._backends.get(backend_id)
        if cls is None:
            log.warning("Unknown backend: %s", backend_id)
            return None
        return cls()

    def available_backends(self) -> list[tuple[str, str, bool]]:
        """Return list of (id, name, is_available)."""
        result = []
        for bid, cls in self._backends.items():
            inst = cls()
            result.append((bid, cls.name, inst.is_available()))
        return result

    def all_ids(self) -> list[str]:
        return list(self._backends.keys())


_registry: GeneratorRegistry | None = None


def get_registry() -> GeneratorRegistry:
    global _registry
    if _registry is None:
        _registry = GeneratorRegistry()
        _register_defaults(_registry)
    return _registry


def _register_defaults(reg: GeneratorRegistry) -> None:
    from .demo_generator import DemoGenerator
    reg.register("demo", DemoGenerator)

    # Conditionally register diffusers-backed generators
    try:
        from .zeroscope_generator import ZeroscopeGenerator
        reg.register("zeroscope", ZeroscopeGenerator)
    except ImportError:
        log.debug("Zeroscope backend unavailable (diffusers not installed)")

    try:
        from .animatediff_generator import AnimateDiffGenerator
        reg.register("animatediff", AnimateDiffGenerator)
    except ImportError:
        log.debug("AnimateDiff backend unavailable")
