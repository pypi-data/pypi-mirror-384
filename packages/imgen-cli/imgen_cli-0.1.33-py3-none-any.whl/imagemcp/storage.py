from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Tuple

from .config import CONFIG_DIR_NAME
from .models import SessionManifest
from ._compat import dataclass

_SLOT_SESSION_PATTERN = re.compile(r"^(?P<slot>[a-z0-9_-]+)_(?P<session>.+)$")


class InvalidPathError(ValueError):
    """Raised when a resolved path escapes the allowed project root."""


@dataclass()
class ProjectPaths:
    project_root: Path
    target_root: Path
    sessions_root: Path
    campaigns_root: Path
    templates_root: Path

    @classmethod
    def create(cls, project_root: Path, target_root: Path) -> "ProjectPaths":
        project_root = project_root.resolve()
        target_root = _ensure_within_root((project_root / target_root).resolve(), project_root)
        sessions_root = _ensure_within_root(
            (project_root / CONFIG_DIR_NAME / ".sessions").resolve(),
            project_root,
        )
        campaigns_root = _ensure_within_root(
            (project_root / CONFIG_DIR_NAME / "campaigns").resolve(),
            project_root,
        )
        templates_root = _ensure_within_root(
            (project_root / CONFIG_DIR_NAME / "templates").resolve(),
            project_root,
        )
        return cls(
            project_root=project_root,
            target_root=target_root,
            sessions_root=sessions_root,
            campaigns_root=campaigns_root,
            templates_root=templates_root,
        )

    def ensure_directories(self) -> None:
        self.target_root.mkdir(parents=True, exist_ok=True)
        self.sessions_root.mkdir(parents=True, exist_ok=True)
        self.campaigns_root.mkdir(parents=True, exist_ok=True)
        self.templates_root.mkdir(parents=True, exist_ok=True)

    def target_for_slot(self, slot: str, extension: str = ".png") -> Path:
        return self.target_root / f"{slot}{extension}"

    def session_dir(self, slot: str, session_id: str) -> Path:
        safe_slot = _validate_slug(slot)
        session_dir = self.sessions_root / f"{safe_slot}_{session_id}"
        return _ensure_within_root(session_dir.resolve(), self.project_root)

    def iter_session_dirs(self) -> Iterator[Tuple[str, Path]]:
        if not self.sessions_root.exists():
            return iter(())
        for item in sorted(self.sessions_root.iterdir()):
            if not item.is_dir():
                continue
            match = _SLOT_SESSION_PATTERN.match(item.name)
            if not match:
                continue
            slot = match.group("slot")
            yield slot, item

    def manifest_path(self, session_dir: Path) -> Path:
        return session_dir / "session.json"

    def campaign_dir(self, campaign_id: str) -> Path:
        return _ensure_within_root((self.campaigns_root / campaign_id).resolve(), self.project_root)

    def campaign_routes_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "routes"

    def campaign_placements_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "placements"

    def campaign_thumbnails_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "thumbnails"

    def campaign_exports_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "exports"

    def campaign_logs_dir(self, campaign_id: str) -> Path:
        return self.campaign_dir(campaign_id) / "logs"


def _validate_slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9_-]+", value):
        raise ValueError(f"Invalid slot id '{value}'. Use lowercase letters, numbers, '-', '_' only.")
    return value


def _ensure_within_root(path: Path, root: Path) -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    if not resolved_path.is_relative_to(resolved_root):
        raise InvalidPathError(f"Path {resolved_path} escapes root {resolved_root}")
    return resolved_path


def write_manifest(manifest: SessionManifest, manifest_path: Path) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as fh:
        json.dump(manifest.to_dict(), fh, indent=2)
        fh.write("\n")


def load_manifest(manifest_path: Path) -> SessionManifest:
    with manifest_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return SessionManifest.from_dict(data)


@dataclass()
class SlotDeletionResult:
    slot: str
    removed_sessions: int
    removed_targets: int


def list_manifests_for_slot(paths: ProjectPaths, slot: str) -> List[SessionManifest]:
    manifests: List[SessionManifest] = []
    safe_slot = _validate_slug(slot)
    if not paths.sessions_root.exists():
        return manifests
    for dir_path in sorted(paths.sessions_root.glob(f"{safe_slot}_*")):
        manifest_path = paths.manifest_path(dir_path)
        if manifest_path.exists():
            manifests.append(load_manifest(manifest_path))
    return manifests


def list_all_slots(paths: ProjectPaths) -> Dict[str, List[SessionManifest]]:
    result: Dict[str, List[SessionManifest]] = {}
    if not paths.sessions_root.exists():
        return result
    for slot, session_dir in paths.iter_session_dirs():
        manifest_path = paths.manifest_path(session_dir)
        if not manifest_path.exists():
            continue
        manifest = load_manifest(manifest_path)
        key = manifest.slot or slot
        result.setdefault(key, []).append(manifest)
    return result


def most_recent_session(manifests: Iterable[SessionManifest]) -> Optional[SessionManifest]:
    latest: Optional[SessionManifest] = None
    for manifest in manifests:
        if latest is None or manifest.completed_at > latest.completed_at:
            latest = manifest
    return latest


def delete_slot(paths: ProjectPaths, slot: str) -> SlotDeletionResult:
    safe_slot = _validate_slug(slot)
    manifests = list_manifests_for_slot(paths, safe_slot)
    target_paths = set()
    for manifest in manifests:
        for candidate in (manifest.selected_path, manifest.target_path):
            if not candidate:
                continue
            target = (paths.project_root / candidate).resolve()
            try:
                target.relative_to(paths.project_root)
            except ValueError:
                continue
            target_paths.add(target)
    # Always include the default target path in case no manifest exists.
    default_target = paths.target_for_slot(safe_slot)
    target_paths.add(default_target)

    removed_targets = 0
    for path in target_paths:
        if path.exists() and path.is_file():
            path.unlink()
            removed_targets += 1

    session_dirs = list(paths.sessions_root.glob(f"{safe_slot}_*"))
    removed_sessions = 0
    for session_dir in session_dirs:
        if session_dir.is_dir():
            shutil.rmtree(session_dir)
            removed_sessions += 1

    return SlotDeletionResult(slot=safe_slot, removed_sessions=removed_sessions, removed_targets=removed_targets)


__all__ = [
    "ProjectPaths",
    "InvalidPathError",
    "write_manifest",
    "load_manifest",
    "SlotDeletionResult",
    "list_manifests_for_slot",
    "list_all_slots",
    "most_recent_session",
    "delete_slot",
]
