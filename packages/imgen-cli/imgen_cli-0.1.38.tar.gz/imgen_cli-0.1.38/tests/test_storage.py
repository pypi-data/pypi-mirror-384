from __future__ import annotations

from pathlib import Path

from imagemcp.models import (
    EffectiveParameters,
    ImageRecord,
    SessionManifest,
    SessionRequest,
    utc_now,
)
from imagemcp.storage import ProjectPaths, delete_slot, write_manifest


def _build_manifest(paths: ProjectPaths, slot: str, session_id: str, target_rel: str) -> SessionManifest:
    session_dir = paths.session_dir(slot, session_id)
    session_dir_rel = session_dir.relative_to(paths.project_root)
    now = utc_now()
    return SessionManifest(
        slot=slot,
        session_id=session_id,
        target_path=target_rel,
        session_dir=str(session_dir_rel),
        request=SessionRequest(request_text=f"Request for {slot}"),
        effective=EffectiveParameters(
            prompt=f"Prompt for {slot}",
            n=1,
            size="400x400",
            provider="mock",
            model="mock/image",
            generator="mock",
        ),
        images=[
            ImageRecord(
                filename=f"{slot}-0.png",
                media_type="image/png",
                width=400,
                height=400,
                sha256=f"sha256-{slot}",
            )
        ],
        selected_index=0,
        selected_path=target_rel,
        created_at=now,
        completed_at=now,
        history=[],
        warnings=[],
    )


def test_delete_slot_removes_targets_and_sessions(tmp_path):
    project_root = tmp_path
    paths = ProjectPaths.create(project_root, Path("assets"))
    paths.ensure_directories()

    slot = "testimonial"
    session_id = "session123"
    session_dir = paths.session_dir(slot, session_id)
    session_dir.mkdir(parents=True)
    (session_dir / "testimonial-0.png").write_bytes(b"variant")

    manifest = _build_manifest(paths, slot, session_id, "assets/testimonial.webp")
    write_manifest(manifest, paths.manifest_path(session_dir))

    target_path = (project_root / manifest.selected_path).resolve()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_bytes(b"target")

    other_slot = "hero"
    other_session_dir = paths.session_dir(other_slot, "session999")
    other_session_dir.mkdir(parents=True)
    (other_session_dir / "keep.txt").write_text("keep")
    other_target = paths.target_for_slot(other_slot)
    other_target.parent.mkdir(parents=True, exist_ok=True)
    other_target.write_text("keep target")

    result = delete_slot(paths, slot)

    assert result.slot == slot
    assert result.removed_sessions == 1
    assert result.removed_targets == 1
    assert not session_dir.exists()
    assert not target_path.exists()
    assert other_session_dir.exists()
    assert other_target.exists()


def test_delete_slot_handles_missing_data(tmp_path):
    project_root = tmp_path
    paths = ProjectPaths.create(project_root, Path("assets"))
    paths.ensure_directories()

    result = delete_slot(paths, "unknown")

    assert result.slot == "unknown"
    assert result.removed_sessions == 0
    assert result.removed_targets == 0
