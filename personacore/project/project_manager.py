"""Project save/load/history management."""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from personacore.logging_module import get_logger

log = get_logger("project")


@dataclass
class Project:
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = "Untitled Project"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    raw_prompt: str = ""
    enriched_prompt: str = ""
    technical_prompt: str = ""

    persona_id: str = "director"
    model: str = ""
    style_preset: str = "cinematic"

    video_params: dict[str, Any] = field(default_factory=dict)
    output_paths: list[str] = field(default_factory=list)

    history: list[dict[str, Any]] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Project":
        known = {k for k in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in d.items() if k in known})

    def add_history_entry(self, kind: str, data: dict[str, Any]) -> None:
        self.history.append({
            "timestamp": datetime.now().isoformat(),
            "kind": kind,
            **data,
        })
        self.updated_at = datetime.now().isoformat()

    @property
    def has_output(self) -> bool:
        return bool(self.output_paths)

    @property
    def latest_output(self) -> Path | None:
        if self.output_paths:
            p = Path(self.output_paths[-1])
            if p.exists():
                return p
        return None


class ProjectManager:
    """Creates, opens, saves, and lists projects."""

    def __init__(self, projects_dir: Path) -> None:
        self._dir = projects_dir
        self._current: Project | None = None

    @property
    def current(self) -> Project | None:
        return self._current

    @property
    def projects_dir(self) -> Path:
        return self._dir

    def new_project(self, name: str = "Untitled Project") -> Project:
        project = Project(name=name)
        self._current = project
        self._save_project(project)
        log.info("Created project: %s (%s)", project.name, project.id)
        return project

    def open_project(self, project_id: str) -> Project | None:
        path = self._project_path(project_id)
        if not path.exists():
            return None
        try:
            with path.open(encoding="utf-8") as f:
                data = json.load(f)
            project = Project.from_dict(data)
            self._current = project
            log.info("Opened project: %s", project.name)
            return project
        except Exception as e:
            log.error("Failed to open project %s: %s", project_id, e)
            return None

    def save_current(self) -> bool:
        if self._current is None:
            return False
        return self._save_project(self._current)

    def _save_project(self, project: Project) -> bool:
        project.updated_at = datetime.now().isoformat()
        project_dir = self._dir / project.id
        project_dir.mkdir(parents=True, exist_ok=True)
        path = project_dir / "project.json"
        try:
            with path.open("w", encoding="utf-8") as f:
                json.dump(project.to_dict(), f, indent=2)
            return True
        except Exception as e:
            log.error("Failed to save project: %s", e)
            return False

    def list_projects(self) -> list[Project]:
        projects = []
        for d in self._dir.iterdir():
            if d.is_dir():
                path = d / "project.json"
                if path.exists():
                    try:
                        with path.open(encoding="utf-8") as f:
                            data = json.load(f)
                        projects.append(Project.from_dict(data))
                    except Exception:
                        pass
        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    def delete_project(self, project_id: str) -> bool:
        project_dir = self._dir / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)
            if self._current and self._current.id == project_id:
                self._current = None
            return True
        return False

    def get_output_dir(self, project: Project) -> Path:
        d = self._dir / project.id / "outputs"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def export_bundle(self, project: Project, dest_path: Path) -> bool:
        """Package project as a zip bundle."""
        project_dir = self._dir / project.id
        if not project_dir.exists():
            return False
        try:
            shutil.make_archive(
                str(dest_path.with_suffix("")),
                "zip",
                root_dir=str(project_dir),
            )
            return True
        except Exception as e:
            log.error("Export failed: %s", e)
            return False

    def _project_path(self, project_id: str) -> Path:
        return self._dir / project_id / "project.json"
