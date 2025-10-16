"""ImageMCP local tooling package."""

from .ids import make_session_id
from .sessions import SessionContext, SessionManager
from .slot_index import SlotSummary, build_slot_index
from .storage import InvalidPathError, ProjectPaths

from .planner import (
    CollectContextPayload,
    PlanPayload,
    PlanConstraints,
    normalize_collect_context_payload,
    normalize_plan_payload,
)
from .config import (
    ProjectConfig,
    ProjectIndexEntry,
    ensure_project_config,
    load_project_config,
    register_project,
    load_project_index,
    get_project_index_path,
    discover_project_root,
)

__all__ = [
    "SessionContext",
    "SessionManager",
    "ProjectPaths",
    "InvalidPathError",
    "SlotSummary",
    "build_slot_index",
    "make_session_id",
    "CollectContextPayload",
    "PlanPayload",
    "PlanConstraints",
    "normalize_collect_context_payload",
    "normalize_plan_payload",
    "ProjectConfig",
    "ProjectIndexEntry",
    "ensure_project_config",
    "load_project_config",
    "register_project",
    "load_project_index",
    "get_project_index_path",
    "discover_project_root",
]
