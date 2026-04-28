from __future__ import annotations

from personacore.config import settings as settings_module


def test_settings_data_dir_can_be_overridden(tmp_path, monkeypatch) -> None:
    data_dir = tmp_path / "personacore-data"
    monkeypatch.setenv("PERSONACORE_DATA_DIR", str(data_dir))
    settings_module.Settings._instance = None
    settings_module._settings = None

    settings = settings_module.get_settings()

    assert settings.config_dir == data_dir
    assert settings.projects_dir == data_dir / "projects"

    settings_module.Settings._instance = None
    settings_module._settings = None
