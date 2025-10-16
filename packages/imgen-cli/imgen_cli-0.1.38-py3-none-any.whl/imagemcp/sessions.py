from __future__ import annotations

from ._compat import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from .files import atomic_copy, compute_sha256
from .generator import GeneratedImageArtifacts
from .models import (
    EffectiveParameters,
    ImageRecord,
    SessionManifest,
    SessionRequest,
    utc_now,
)
from .storage import ProjectPaths, load_manifest, write_manifest


@dataclass()
class SessionContext:
    slot: str
    session_id: str
    session_dir: Path
    manifest_path: Path
    target_path: Path
    target_path_str: str


class SessionManager:
    def __init__(self, paths: ProjectPaths) -> None:
        self.paths = paths

    def create_context(self, slot: str, session_id: str) -> SessionContext:
        session_dir = self.paths.session_dir(slot, session_id)
        manifest_path = self.paths.manifest_path(session_dir)
        target_path = self.paths.target_for_slot(slot)
        target_path_str = str(target_path.relative_to(self.paths.project_root))
        return SessionContext(
            slot=slot,
            session_id=session_id,
            session_dir=session_dir,
            manifest_path=manifest_path,
            target_path=target_path,
            target_path_str=target_path_str,
        )

    def ensure_session_dir(self, ctx: SessionContext) -> None:
        ctx.session_dir.mkdir(parents=True, exist_ok=True)

    def build_manifest(
        self,
        ctx: SessionContext,
        request: SessionRequest,
        effective: EffectiveParameters,
        image_artifacts: Iterable[GeneratedImageArtifacts],
        warnings: Optional[List[str]] = None,
        auto_selected_index: int = 0,
        created_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
    ) -> SessionManifest:
        created_at = created_at or utc_now()
        completed_at = completed_at or created_at
        images: List[ImageRecord] = []
        for artifact in image_artifacts:
            processed_path = artifact.processed_path
            media_type = artifact.media_type or _guess_media_type(processed_path)
            images.append(
                ImageRecord(
                    filename=processed_path.name,
                    media_type=media_type,
                    width=artifact.processed_width,
                    height=artifact.processed_height,
                    sha256=compute_sha256(processed_path),
                    original_width=artifact.original_width,
                    original_height=artifact.original_height,
                    raw_filename=artifact.raw_filename,
                    crop_fraction=artifact.crop_fraction,
                )
            )
        manifest = SessionManifest(
            slot=ctx.slot,
            session_id=ctx.session_id,
            target_path=ctx.target_path_str,
            session_dir=str(ctx.session_dir.relative_to(self.paths.project_root)),
            request=request,
            effective=effective,
            images=images,
            selected_index=auto_selected_index,
            selected_path=ctx.target_path_str,
            created_at=created_at,
            completed_at=completed_at,
            history=[],
            warnings=warnings or [],
        )
        return manifest

    def promote_variant(self, ctx: SessionContext, manifest: SessionManifest, index: int) -> None:
        image = manifest.images[index]
        source = ctx.session_dir / image.filename
        atomic_copy(source, ctx.target_path)
        manifest.record_selection(index)
        manifest.selected_path = ctx.target_path_str
        manifest.completed_at = utc_now()
        write_manifest(manifest, ctx.manifest_path)

    def read_manifest(self, ctx: SessionContext) -> SessionManifest:
        return load_manifest(ctx.manifest_path)


def _guess_media_type(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in {".png"}:
        return "image/png"
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"

__all__ = [
    "SessionManager",
    "SessionContext",
]
