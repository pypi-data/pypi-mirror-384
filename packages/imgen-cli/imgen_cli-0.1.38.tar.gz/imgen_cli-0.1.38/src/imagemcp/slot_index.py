from __future__ import annotations

from ._compat import dataclass
from datetime import datetime
from typing import Dict, List, Optional

from .models import SessionManifest
from .storage import ProjectPaths, list_all_slots, most_recent_session


@dataclass()
class SlotSummary:
    slot: str
    session_count: int
    selected_path: Optional[str]
    selected_index: Optional[int]
    last_updated: Optional[datetime]
    warnings: List[str]


def build_slot_index(paths: ProjectPaths) -> Dict[str, SlotSummary]:
    result: Dict[str, SlotSummary] = {}
    grouped = list_all_slots(paths)
    for slot, manifests in grouped.items():
        manifests.sort(key=lambda m: m.completed_at)
        latest = most_recent_session(manifests)
        summary = SlotSummary(
            slot=slot,
            session_count=len(manifests),
            selected_path=latest.selected_path if latest else None,
            selected_index=latest.selected_index if latest else None,
            last_updated=latest.completed_at if latest else None,
            warnings=_collect_warnings(manifests),
        )
        result[slot] = summary
    return result


def _collect_warnings(manifests: List[SessionManifest]) -> List[str]:
    warnings: List[str] = []
    for manifest in manifests:
        warnings.extend(manifest.warnings)
    return warnings


__all__ = ["SlotSummary", "build_slot_index"]
