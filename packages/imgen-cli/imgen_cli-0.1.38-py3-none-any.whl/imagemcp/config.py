from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

CONFIG_DIR_NAME = ".imagemcp"
CONFIG_FILENAME = "config.json"
PROJECT_SCHEMA = "imagemcp-project@1"
INDEX_SCHEMA = "imagemcp-project-index@1"
DEFAULT_TARGET_ROOT = "public/img"
DEFAULT_PROJECT_NAME = "ImageMCP Project"
DEFAULT_GALLERY_HOST = "localhost"
DEFAULT_GALLERY_PORT = 8765


@dataclass
class ProjectConfig:
    project_root: Path
    project_id: str
    project_name: str
    target_root: str
    gallery_host: str = DEFAULT_GALLERY_HOST
    gallery_port: int = DEFAULT_GALLERY_PORT
    schema: str = PROJECT_SCHEMA
    created_at: str = field(default_factory=lambda: _timestamp())
    updated_at: str = field(default_factory=lambda: _timestamp())

    def config_path(self) -> Path:
        return self.project_root / CONFIG_DIR_NAME / CONFIG_FILENAME

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema": self.schema,
            "projectId": self.project_id,
            "projectName": self.project_name,
            "targetRoot": self.target_root,
            "gallery": {
                "host": self.gallery_host,
                "port": self.gallery_port,
            },
            "createdAt": self.created_at,
            "updatedAt": self.updated_at,
        }

    def touch(self) -> None:
        self.updated_at = _timestamp()


@dataclass
class ProjectIndexEntry:
    project_id: str
    project_name: str
    project_root: Path
    target_root: str
    gallery_host: str = DEFAULT_GALLERY_HOST
    gallery_port: int = DEFAULT_GALLERY_PORT
    last_used_at: str = field(default_factory=lambda: _timestamp())

    def to_dict(self) -> Dict[str, object]:
        return {
            "projectId": self.project_id,
            "projectName": self.project_name,
            "projectRoot": str(self.project_root),
            "targetRoot": self.target_root,
            "gallery": {
                "host": self.gallery_host,
                "port": self.gallery_port,
            },
            "lastUsedAt": self.last_used_at,
        }


def discover_project_root(start: Path) -> Optional[Path]:
    current = start.resolve()
    for path in [current] + list(current.parents):
        candidate = path / CONFIG_DIR_NAME / CONFIG_FILENAME
        if candidate.exists():
            return path
    return None


def ensure_project_config(
    start_root: Path,
    target_root: Optional[str] = None,
    project_name: Optional[str] = None,
) -> ProjectConfig:
    project_root = discover_project_root(start_root) or start_root.resolve()
    config_path = project_root / CONFIG_DIR_NAME / CONFIG_FILENAME
    normalized_target_root: Optional[str] = None
    if target_root:
        candidate = Path(target_root)
        try:
            if candidate.is_absolute():
                resolved = candidate.resolve()
            else:
                resolved = (project_root / candidate).resolve()
        except OSError:
            resolved = candidate if candidate.is_absolute() else project_root / candidate
        if resolved.is_absolute():
            try:
                relative = resolved.relative_to(project_root)
            except ValueError:
                normalized_target_root = str(resolved)
            else:
                normalized_target_root = relative.as_posix()
        else:
            normalized_target_root = resolved.as_posix()
    if normalized_target_root:
        target_root = normalized_target_root
    if config_path.exists():
        config = _load_config(config_path, project_root)
        updated = False
        if target_root and target_root != config.target_root:
            config.target_root = target_root
            updated = True
        if project_name and project_name != config.project_name:
            config.project_name = project_name
            updated = True
        if updated:
            config.touch()
            save_project_config(config)
        return config

    generated_name = project_name or _default_project_name(project_root)
    slug = _slugify(generated_name)
    config = ProjectConfig(
        project_root=project_root,
        project_id=slug,
        project_name=generated_name,
        target_root=target_root or DEFAULT_TARGET_ROOT,
    )
    save_project_config(config)
    return config


def load_project_config(project_root: Path) -> ProjectConfig:
    project_root = project_root.resolve()
    config_path = project_root / CONFIG_DIR_NAME / CONFIG_FILENAME
    if not config_path.exists():
        raise FileNotFoundError(f"Project config not found at {config_path}")
    return _load_config(config_path, project_root)


def save_project_config(config: ProjectConfig) -> None:
    config_dir = config.project_root / CONFIG_DIR_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    config.touch()
    with (config_dir / CONFIG_FILENAME).open("w", encoding="utf-8") as fh:
        json.dump(config.to_dict(), fh, indent=2)
        fh.write("\n")
    register_project(config)


def register_project(config: ProjectConfig) -> None:
    index_path = get_project_index_path()
    try:
        index_path.parent.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        return
    try:
        with index_path.open("r", encoding="utf-8") as fh:
            existing = json.load(fh)
    except FileNotFoundError:
        existing = {"schema": INDEX_SCHEMA, "projects": []}
    except json.JSONDecodeError:
        existing = {"schema": INDEX_SCHEMA, "projects": []}

    projects = existing.get("projects", [])
    now = _timestamp()
    entry_dict = {
        "projectId": config.project_id,
        "projectName": config.project_name,
        "projectRoot": str(config.project_root),
        "targetRoot": config.target_root,
        "gallery": {
            "host": config.gallery_host,
            "port": config.gallery_port,
        },
        "lastUsedAt": now,
    }
    index_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with index_path.open("r", encoding="utf-8") as fh:
            existing = json.load(fh)
    except FileNotFoundError:
        existing = {"schema": INDEX_SCHEMA, "projects": []}
    except json.JSONDecodeError:
        existing = {"schema": INDEX_SCHEMA, "projects": []}

    projects = existing.get("projects", [])
    now = _timestamp()
    entry_dict = {
        "projectId": config.project_id,
        "projectName": config.project_name,
        "projectRoot": str(config.project_root),
        "targetRoot": config.target_root,
        "gallery": {
            "host": config.gallery_host,
            "port": config.gallery_port,
        },
        "lastUsedAt": now,
    }
    found = False
    for index, project in enumerate(projects):
        if project.get("projectId") == config.project_id or project.get("projectRoot") == str(config.project_root):
            projects[index] = entry_dict
            found = True
            break
    if not found:
        projects.append(entry_dict)
    existing["schema"] = INDEX_SCHEMA
    existing["projects"] = projects
    try:
        with index_path.open("w", encoding="utf-8") as fh:
            json.dump(existing, fh, indent=2)
            fh.write("\n")
    except PermissionError:
        pass


def load_project_index() -> List[ProjectIndexEntry]:
    index_path = get_project_index_path()
    if not index_path.exists():
        return []
    try:
        with index_path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        return []
    entries: List[ProjectIndexEntry] = []
    for project in data.get("projects", []):
        try:
            entries.append(
                ProjectIndexEntry(
                    project_id=project["projectId"],
                    project_name=project.get("projectName", DEFAULT_PROJECT_NAME),
                    project_root=Path(project["projectRoot"]).resolve(),
                    target_root=project.get("targetRoot", DEFAULT_TARGET_ROOT),
                    gallery_host=project.get("gallery", {}).get("host", DEFAULT_GALLERY_HOST),
                    gallery_port=int(project.get("gallery", {}).get("port", DEFAULT_GALLERY_PORT)),
                    last_used_at=project.get("lastUsedAt", _timestamp()),
                )
            )
        except KeyError:
            continue
    return entries


def get_project_index_path() -> Path:
    return Path.home() / CONFIG_DIR_NAME / "projects.json"


def _load_config(config_path: Path, project_root: Path) -> ProjectConfig:
    with config_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    gallery = data.get("gallery", {})
    return ProjectConfig(
        project_root=project_root,
        project_id=data.get("projectId", _slugify(project_root.name)),
        project_name=data.get("projectName", _default_project_name(project_root)),
        target_root=data.get("targetRoot", DEFAULT_TARGET_ROOT),
        gallery_host=gallery.get("host", DEFAULT_GALLERY_HOST),
        gallery_port=int(gallery.get("port", DEFAULT_GALLERY_PORT)),
        schema=data.get("schema", PROJECT_SCHEMA),
        created_at=data.get("createdAt", _timestamp()),
        updated_at=data.get("updatedAt", _timestamp()),
    )


def _timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"


def _slugify(value: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", value.strip().lower()).strip("-")
    return slug or "project"


def _default_project_name(project_root: Path) -> str:
    name = project_root.name or DEFAULT_PROJECT_NAME
    return name.replace("-", " ").replace("_", " ") or DEFAULT_PROJECT_NAME


__all__ = [
    "ProjectConfig",
    "ProjectIndexEntry",
    "ensure_project_config",
    "load_project_config",
    "save_project_config",
    "register_project",
    "load_project_index",
    "get_project_index_path",
    "discover_project_root",
    "CONFIG_DIR_NAME",
    "CONFIG_FILENAME",
]
