__all__ = [
    "TitleBar",
    "SidebarPanel",
    "PromptStudio",
    "StepTracker",
    "SettingsPanel",
    "LogConsole",
    "VideoPreviewWidget",
]

_EXPORTS = {
    "TitleBar": (".title_bar", "TitleBar"),
    "SidebarPanel": (".sidebar", "SidebarPanel"),
    "PromptStudio": (".prompt_studio", "PromptStudio"),
    "StepTracker": (".step_tracker", "StepTracker"),
    "SettingsPanel": (".settings_panel", "SettingsPanel"),
    "LogConsole": (".log_console", "LogConsole"),
    "VideoPreviewWidget": (".video_preview", "VideoPreviewWidget"),
}


def __getattr__(name: str):
    if name in _EXPORTS:
        from importlib import import_module

        module_name, attr_name = _EXPORTS[name]
        module = import_module(module_name, __name__)
        return getattr(module, attr_name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
