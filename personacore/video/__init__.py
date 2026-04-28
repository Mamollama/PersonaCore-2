__all__ = [
    "BaseVideoGenerator",
    "GenerationParams",
    "GenerationResult",
    "GeneratorRegistry",
    "get_registry",
    "FFmpegPipeline",
    "DemoGenerator",
]

_EXPORTS = {
    "BaseVideoGenerator": (".base_generator", "BaseVideoGenerator"),
    "GenerationParams": (".base_generator", "GenerationParams"),
    "GenerationResult": (".base_generator", "GenerationResult"),
    "GeneratorRegistry": (".registry", "GeneratorRegistry"),
    "get_registry": (".registry", "get_registry"),
    "FFmpegPipeline": (".ffmpeg_pipeline", "FFmpegPipeline"),
    "DemoGenerator": (".demo_generator", "DemoGenerator"),
}


def __getattr__(name: str):
    if name in _EXPORTS:
        from importlib import import_module

        module_name, attr_name = _EXPORTS[name]
        module = import_module(module_name, __name__)
        return getattr(module, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
