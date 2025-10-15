from __future__ import annotations

import http.server
import json
import mimetypes
import socketserver
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import SessionManager, build_slot_index
from .config import (
    ProjectConfig,
    ensure_project_config,
    get_project_index_path,
    load_project_index,
    register_project,
)
from .models import format_ts
from .storage import (
    InvalidPathError,
    ProjectPaths,
    delete_slot,
    list_manifests_for_slot,
    load_manifest,
)
from .campaign import build_campaign_status
from .campaign.workspace import CampaignWorkspace
from .campaign.schemas import (
    CampaignConfig,
    CampaignRoute,
    ExportManifest,
    PlacementManifest,
    ReviewState,
    RouteSeed,
)


ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.strptime(value, ISO_FORMAT)
    except Exception:  # pragma: no cover - fallback for unexpected formats
        return None


def _format_optional_timestamp(value: Optional[datetime]) -> Optional[str]:
    if value is None:
        return None
    return format_ts(value)


def _as_review_state(value) -> str:
    if isinstance(value, ReviewState):
        return value.value
    return str(value)


def _format_variant_label(index: int) -> str:
    return f"v{index + 1:03d}"


def _status_resume_hint(report) -> Optional[Dict[str, object]]:
    pending = getattr(report, "pending", [])
    if not pending:
        return None
    first = pending[0]
    return {
        "routeId": first.route_id,
        "placementId": first.placement_id,
        "variantIndex": first.variant_index,
        "variantLabel": _format_variant_label(first.variant_index),
    }


def _status_alerts(report) -> List[Dict[str, object]]:
    alerts: List[Dict[str, object]] = []

    missing_manifests = getattr(report, "missing_manifests", []) or []
    for path in missing_manifests:
        alerts.append({
            "type": "missingManifest",
            "manifestPath": path,
        })

    orphan_files = getattr(report, "orphan_files", []) or []
    for path in orphan_files:
        alerts.append({
            "type": "orphanFile",
            "path": path,
        })

    pending_counts: Dict[str, int] = {}
    for item in getattr(report, "pending", []) or []:
        placement_id = item.placement_id
        pending_counts[placement_id] = pending_counts.get(placement_id, 0) + 1
    for placement_id, count in sorted(pending_counts.items(), key=lambda kv: kv[0]):
        alerts.append({
            "type": "pendingVariants",
            "placementId": placement_id,
            "count": count,
        })

    placements = getattr(report, "placements", []) or []
    for placement in placements:
        expected = getattr(placement, "expected_variants", 0) or 0
        generated = getattr(placement, "generated_variants", 0) or 0
        if expected and not generated:
            alerts.append({
                "type": "awaitingGeneration",
                "placementId": placement.placement_id,
                "expectedVariants": expected,
            })

    return alerts


def _status_progress(report) -> Dict[str, object]:
    totals = getattr(report, "totals", None)
    if totals is None:
        return {
            "expectedVariants": 0,
            "generatedVariants": 0,
            "pendingVariants": 0,
            "extraVariants": 0,
            "progressPercent": 0.0,
        }
    expected = totals.expected_variants or 0
    generated = totals.generated_variants or 0
    pending = totals.pending_variants or 0
    extra = totals.extra_generated or 0
    progress_percent = 0.0
    if expected:
        progress_percent = max(0.0, min(100.0, (generated / expected) * 100.0))
    return {
        "expectedVariants": expected,
        "generatedVariants": generated,
        "pendingVariants": pending,
        "extraVariants": extra,
        "progressPercent": progress_percent,
    }


def _iter_campaign_workspaces(paths: ProjectPaths) -> Iterable[CampaignWorkspace]:
    campaigns_root = paths.campaigns_root
    if not campaigns_root.exists():
        return []
    workspaces: List[CampaignWorkspace] = []
    for entry in sorted(campaigns_root.iterdir()):
        if not entry.is_dir():
            continue
        workspace = CampaignWorkspace(paths, entry.name)
        if workspace.config_path.exists():
            workspaces.append(workspace)
    return workspaces


def _collect_routes(config: CampaignConfig, workspace: CampaignWorkspace) -> Dict[str, Dict[str, object]]:
    routes: Dict[str, Dict[str, object]] = {}
    try:
        for route in workspace.iter_routes() or []:
            routes[route.route_id] = {
                "routeId": route.route_id,
                "name": route.name,
                "summary": route.summary,
                "status": _as_review_state(route.status),
                "source": route.source,
                "promptTemplate": route.prompt_template,
                "promptTokens": list(route.prompt_tokens),
                "copyTokens": list(route.copy_tokens),
                "assetRefs": list(route.asset_refs),
            }
    except Exception:
        # Keep partial data if any route file fails to parse
        pass

    for seed in config.routes:
        if seed.route_id in routes:
            continue
        routes[seed.route_id] = {
            "routeId": seed.route_id,
            "name": seed.name,
            "summary": seed.summary,
            "status": _as_review_state(seed.status),
            "source": "seed",
            "promptTemplate": None,
            "promptTokens": list(seed.prompt_tokens),
            "copyTokens": list(seed.copy_tokens),
            "assetRefs": [],
        }
    return routes


def _collect_manifests(workspace: CampaignWorkspace) -> Dict[str, PlacementManifest]:
    manifests: Dict[str, PlacementManifest] = {}
    try:
        for manifest in workspace.iter_manifests() or []:
            manifests[manifest.placement_id] = manifest
    except Exception:
        pass
    return manifests


def _placement_state_counts(manifest: PlacementManifest) -> Dict[str, int]:
    counts: Dict[str, int] = {state.value: 0 for state in ReviewState}
    for route_entry in manifest.routes:
        for variant in route_entry.variants:
            state_key = _as_review_state(variant.review_state)
            counts[state_key] = counts.get(state_key, 0) + 1
    return counts


def _build_campaign_summary(workspace: CampaignWorkspace, project_id: str) -> Dict[str, object]:
    try:
        config = workspace.load_config()
    except Exception:
        return {}

    status_report = None
    try:
        status_report = build_campaign_status(workspace)
    except Exception:
        status_report = None

    manifests = _collect_manifests(workspace)
    total_variants = 0
    counts: Dict[str, int] = {state.value: 0 for state in ReviewState}
    latest = None
    for manifest in manifests.values():
        updated_at = _parse_timestamp(manifest.updated_at)
        if updated_at and (latest is None or updated_at > latest):
            latest = updated_at
        for route_entry in manifest.routes:
            for variant in route_entry.variants:
                total_variants += 1
                state_key = _as_review_state(variant.review_state)
                counts[state_key] = counts.get(state_key, 0) + 1

    routes_count = len(_collect_routes(config, workspace))
    if status_report is not None:
        placements_count = len(status_report.placements)
    else:
        placements_count = len(config.placements) or len(manifests)
    approved = counts.get(ReviewState.APPROVED.value, 0)

    progress = _status_progress(status_report)
    resume_hint = _status_resume_hint(status_report) if status_report else None
    alerts = _status_alerts(status_report) if status_report else []
    missing_manifests = list(getattr(status_report, "missing_manifests", []) or [])
    orphan_files = list(getattr(status_report, "orphan_files", []) or [])

    summary = {
        "projectId": project_id,
        "campaignId": config.campaign_id,
        "name": config.name,
        "status": _as_review_state(config.status),
        "tags": list(config.tags),
        "routes": routes_count,
        "placements": placements_count,
        "variants": total_variants,
        "approved": approved,
        "pending": counts.get(ReviewState.PENDING.value, 0),
        "revise": counts.get(ReviewState.REVISE.value, 0),
        "defaultProvider": config.default_provider,
        "updatedAt": _format_optional_timestamp(latest),
        "progress": progress,
        "expectedVariants": progress.get("expectedVariants"),
        "generatedVariants": progress.get("generatedVariants"),
        "pendingVariants": progress.get("pendingVariants"),
        "extraVariants": progress.get("extraVariants"),
        "resume": resume_hint,
        "alerts": alerts,
        "missingManifests": missing_manifests,
        "orphanFiles": orphan_files,
    }
    return summary


def _campaign_export_entries(workspace: CampaignWorkspace) -> List[Dict[str, object]]:
    entries: List[Dict[str, object]] = []
    exports_dir = workspace.exports_dir
    if not exports_dir.exists():
        return entries
    for manifest_path in sorted(exports_dir.rglob("manifest.json")):
        try:
            export_manifest = workspace.load_export_manifest(manifest_path)
        except Exception:
            continue
        entries.append(
            {
                "platform": export_manifest.platform,
                "exportId": export_manifest.export_id,
                "generatedAt": export_manifest.generated_at,
                "includeStates": [
                    _as_review_state(state) for state in (export_manifest.include_states or [])
                ],
                "fileCount": len(export_manifest.files),
                "csvFiles": [
                    {
                        "name": csv_file.name,
                        "path": csv_file.path,
                        "rowCount": csv_file.row_count,
                    }
                    for csv_file in export_manifest.csv_files
                ],
                "manifestPath": str(manifest_path.relative_to(workspace.root)),
            }
        )
    entries.sort(key=lambda item: item.get("generatedAt") or "", reverse=True)
    return entries


def _campaign_log_entries(workspace: CampaignWorkspace) -> List[Dict[str, object]]:
    logs: List[Dict[str, object]] = []
    logs_dir = workspace.logs_dir
    if not logs_dir.exists():
        return logs
    for log_path in sorted(logs_dir.glob("batch-*.jsonl")):
        try:
            stat = log_path.stat()
        except OSError:
            continue
        updated_at = datetime.utcfromtimestamp(stat.st_mtime)
        logs.append(
            {
                "filename": log_path.name,
                "updatedAt": format_ts(updated_at),
                "sizeBytes": stat.st_size,
                "relativePath": str(log_path.relative_to(workspace.root)),
            }
        )
    logs.sort(key=lambda item: item.get("updatedAt") or "", reverse=True)
    return logs


def _build_campaign_detail(workspace: CampaignWorkspace, project_id: str) -> Dict[str, object]:
    try:
        config = workspace.load_config()
    except Exception:
        return {}

    status_report = None
    try:
        status_report = build_campaign_status(workspace)
    except Exception:
        status_report = None

    routes_map = _collect_routes(config, workspace)
    manifests = _collect_manifests(workspace)
    placement_status_lookup: Dict[str, object] = {}
    route_placement_lookup: Dict[tuple[str, str], object] = {}
    if status_report is not None:
        placement_status_lookup = {
            placement.placement_id: placement for placement in status_report.placements
        }
        for route_status in status_report.routes:
            for placement_status in route_status.placements:
                route_placement_lookup[(placement_status.placement_id, route_status.route_id)] = (
                    placement_status
                )

    placement_entries: List[Dict[str, object]] = []
    seen_placements: set[str] = set()
    for placement in config.placements:
        placement_id = placement.override_id or placement.template_id
        seen_placements.add(placement_id)
        manifest = manifests.get(placement_id)
        counts = {state.value: 0 for state in ReviewState}
        total = 0
        updated_at = None
        if manifest:
            updated_at = manifest.updated_at
            for route_entry in manifest.routes:
                for variant in route_entry.variants:
                    total += 1
                    state_key = _as_review_state(variant.review_state)
                    counts[state_key] = counts.get(state_key, 0) + 1
        entry = {
            "placementId": placement_id,
            "templateId": placement.template_id,
            "variants": total,
            "counts": counts,
            "provider": placement.provider,
            "notes": placement.notes,
            "updatedAt": updated_at,
        }
        status_info = placement_status_lookup.get(placement_id)
        if status_info is not None:
            entry["expectedVariants"] = status_info.expected_variants
            entry["generatedVariants"] = status_info.generated_variants
            entry["pendingVariants"] = status_info.pending_variants
            entry["extraVariants"] = status_info.extra_generated
            entry["routesWithOutput"] = status_info.routes_with_output
            entry["routesMissing"] = list(status_info.routes_missing)
            entry["manifestPresent"] = status_info.manifest_present
            entry["manifestPath"] = status_info.manifest_path
            entry["manifestRoutes"] = status_info.manifest_routes
        placement_entries.append(entry)

    # Include manifests that reference placements not in the current config
    for placement_id, manifest in manifests.items():
        if placement_id in seen_placements:
            continue
        counts = {state.value: 0 for state in ReviewState}
        total = 0
        for route_entry in manifest.routes:
            for variant in route_entry.variants:
                total += 1
                state_key = _as_review_state(variant.review_state)
                counts[state_key] = counts.get(state_key, 0) + 1
        entry = {
            "placementId": placement_id,
            "templateId": manifest.template_id,
            "variants": total,
            "counts": counts,
            "provider": None,
            "notes": None,
            "updatedAt": manifest.updated_at,
        }
        status_info = placement_status_lookup.get(placement_id)
        if status_info is not None:
            entry["expectedVariants"] = status_info.expected_variants
            entry["generatedVariants"] = status_info.generated_variants
            entry["pendingVariants"] = status_info.pending_variants
            entry["extraVariants"] = status_info.extra_generated
            entry["routesWithOutput"] = status_info.routes_with_output
            entry["routesMissing"] = list(status_info.routes_missing)
            entry["manifestPresent"] = status_info.manifest_present
            entry["manifestPath"] = status_info.manifest_path
            entry["manifestRoutes"] = status_info.manifest_routes
        placement_entries.append(entry)

    if status_report is not None:
        existing_ids = {entry["placementId"] for entry in placement_entries}
        for placement_id, status_info in placement_status_lookup.items():
            if placement_id in existing_ids:
                continue
            entry = {
                "placementId": placement_id,
                "templateId": status_info.template_id,
                "variants": 0,
                "counts": {state.value: 0 for state in ReviewState},
                "provider": None,
                "notes": None,
                "updatedAt": None,
                "expectedVariants": status_info.expected_variants,
                "generatedVariants": status_info.generated_variants,
                "pendingVariants": status_info.pending_variants,
                "extraVariants": status_info.extra_generated,
                "routesWithOutput": status_info.routes_with_output,
                "routesMissing": list(status_info.routes_missing),
                "manifestPresent": status_info.manifest_present,
                "manifestPath": status_info.manifest_path,
                "manifestRoutes": status_info.manifest_routes,
            }
            placement_entries.append(entry)

    total_variants = 0
    state_totals: Dict[str, int] = {state.value: 0 for state in ReviewState}
    matrix: List[Dict[str, object]] = []

    for placement_id, manifest in manifests.items():
        for route_entry in manifest.routes:
            variants_payload: List[Dict[str, object]] = []
            for variant in route_entry.variants:
                state_key = _as_review_state(variant.review_state)
                state_totals[state_key] = state_totals.get(state_key, 0) + 1
                total_variants += 1
                variants_payload.append(
                    {
                        "variantId": variant.variant_id,
                        "index": variant.index,
                        "file": variant.file,
                        "thumbnail": variant.thumbnail,
                        "reviewState": state_key,
                        "seed": variant.seed,
                        "prompt": variant.prompt,
                        "createdAt": variant.created_at,
                        "notes": variant.review_notes,
                        "provider": variant.provider,
                        "placementId": placement_id,
                        "routeId": route_entry.route_id,
                    }
                )
            matrix.append(
                {
                    "placementId": placement_id,
                    "routeId": route_entry.route_id,
                    "routeSummary": route_entry.summary,
                    "routeStatus": _as_review_state(route_entry.status),
                    "variants": variants_payload,
                }
            )

    matrix_lookup: Dict[tuple[str, str], Dict[str, object]] = {
        (cell["placementId"], cell["routeId"]): cell for cell in matrix
    }

    if status_report is not None:
        for route_status in status_report.routes:
            for rp_status in route_status.placements:
                key = (rp_status.placement_id, route_status.route_id)
                if key not in matrix_lookup:
                    route_meta = routes_map.get(route_status.route_id, {})
                    cell = {
                        "placementId": rp_status.placement_id,
                        "routeId": route_status.route_id,
                        "routeSummary": route_meta.get("summary"),
                        "routeStatus": route_meta.get("status"),
                        "variants": [],
                    }
                    matrix.append(cell)
                    matrix_lookup[key] = cell

        for key, cell in matrix_lookup.items():
            rp_status = route_placement_lookup.get(key)
            if rp_status is not None:
                cell["expectedVariants"] = rp_status.expected_variants
                cell["generatedVariants"] = rp_status.generated_variants
                cell["pendingVariants"] = len(rp_status.pending_variants)
                cell["pendingVariantIndices"] = list(rp_status.pending_variants)
                cell["pendingVariantLabels"] = [
                    _format_variant_label(idx) for idx in rp_status.pending_variants
                ]
                cell["extraVariantIndices"] = list(rp_status.extra_generated)
                cell["extraVariantLabels"] = [
                    _format_variant_label(idx) for idx in rp_status.extra_generated
                ]
                cell["manifestRecorded"] = rp_status.manifest_recorded
                cell["manifestMissing"] = list(rp_status.manifest_missing)
                cell["nextVariantIndex"] = rp_status.next_variant_index
            else:
                cell.setdefault("expectedVariants", 0)
                cell.setdefault("generatedVariants", 0)
                cell.setdefault("pendingVariants", 0)
                cell.setdefault("pendingVariantIndices", [])
                cell.setdefault("pendingVariantLabels", [])
                cell.setdefault("extraVariantIndices", [])
                cell.setdefault("extraVariantLabels", [])
                cell.setdefault("manifestRecorded", 0)
                cell.setdefault("manifestMissing", [])
                cell.setdefault("nextVariantIndex", None)

    # Sort for stable output
    placement_entries.sort(key=lambda item: item["placementId"])
    matrix.sort(key=lambda item: (item["placementId"], item["routeId"]))

    summary_latest = max(
        filter(None, (_parse_timestamp(item.get("updatedAt")) for item in placement_entries)),
        default=None,
    )

    progress = _status_progress(status_report)
    resume_hint = _status_resume_hint(status_report) if status_report else None
    alerts = _status_alerts(status_report) if status_report else []
    missing_manifests = list(getattr(status_report, "missing_manifests", []) or [])
    orphan_files = list(getattr(status_report, "orphan_files", []) or [])

    detail = {
        "campaign": {
            "projectId": project_id,
            "campaignId": config.campaign_id,
            "name": config.name,
            "status": _as_review_state(config.status),
            "tags": list(config.tags),
            "defaultProvider": config.default_provider,
            "notes": config.notes,
            "brief": config.brief.model_dump(mode="python"),
            "variantDefaults": config.variant_defaults.model_dump(mode="python"),
            "updatedAt": _format_optional_timestamp(summary_latest),
        },
        "routes": list(routes_map.values()),
        "placements": placement_entries,
        "matrix": matrix,
        "stats": {
            "total": total_variants,
            "approved": state_totals.get(ReviewState.APPROVED.value, 0),
            "pending": state_totals.get(ReviewState.PENDING.value, 0),
            "revise": state_totals.get(ReviewState.REVISE.value, 0),
        },
        "exports": _campaign_export_entries(workspace),
        "logs": _campaign_log_entries(workspace),
        "progress": progress,
        "resume": resume_hint,
        "alerts": alerts,
        "status": {
            **progress,
            "missingManifests": missing_manifests,
            "orphanFiles": orphan_files,
            "alerts": alerts,
        },
    }
    detail["campaign"]["routesCount"] = len(detail["routes"])
    detail["campaign"]["placementsCount"] = len(detail["placements"])
    if status_report is not None:
        detail["statusReport"] = asdict(status_report)
    return detail


@dataclass
class ProjectInfo:
    project_id: str
    project_name: str
    project_root: Path
    target_root: str


@dataclass
class ProjectContext:
    info: ProjectInfo
    paths: ProjectPaths
    manager: SessionManager


class ProjectRegistry:
    def __init__(self, default_config: ProjectConfig, default_paths: ProjectPaths) -> None:
        self._default_id = default_config.project_id
        self._contexts: Dict[str, ProjectContext] = {}
        self._index_path = get_project_index_path()
        self.register_config(default_config, default_paths)

    def register_config(
        self,
        config: ProjectConfig,
        paths: Optional[ProjectPaths] = None,
    ) -> None:
        info = ProjectInfo(
            project_id=config.project_id,
            project_name=config.project_name,
            project_root=config.project_root,
            target_root=config.target_root,
        )
        if paths is None:
            paths = ProjectPaths.create(config.project_root, Path(config.target_root))
            paths.ensure_directories()
        context = ProjectContext(info=info, paths=paths, manager=SessionManager(paths))
        self._contexts[info.project_id] = context

    def list_projects(self) -> List[ProjectInfo]:
        projects: Dict[str, ProjectInfo] = {
            context.info.project_id: context.info for context in self._contexts.values()
        }
        for entry in load_project_index():
            info = ProjectInfo(
                project_id=entry.project_id,
                project_name=entry.project_name,
                project_root=entry.project_root,
                target_root=entry.target_root,
            )
            projects[info.project_id] = info
        return list(projects.values())

    def get_context(self, project_id: Optional[str]) -> ProjectContext:
        if not project_id:
            project_id = self._default_id
        context = self._contexts.get(project_id)
        if context:
            return context
        for info in self.list_projects():
            if info.project_id == project_id:
                paths = ProjectPaths.create(info.project_root, Path(info.target_root))
                paths.ensure_directories()
                context = ProjectContext(info=info, paths=paths, manager=SessionManager(paths))
                self._contexts[project_id] = context
                return context
        raise KeyError(project_id)

    def default_project(self) -> ProjectInfo:
        return self.get_context(self._default_id).info



class GalleryServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

    def __init__(self, address: tuple[str, int], registry: ProjectRegistry) -> None:
        handler = _make_handler(registry)
        super().__init__(address, handler)
        self.registry = registry


def serve_gallery(
    config: ProjectConfig,
    paths: ProjectPaths,
    host: str = "127.0.0.1",
    port: int = 8765,
) -> None:
    registry = ProjectRegistry(config, paths)
    with GalleryServer((host, port), registry) as server:
        print(f"Gallery serving at http://{host}:{port}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("Stopping gallery...")


def _make_handler(registry: ProjectRegistry):

    class Handler(http.server.BaseHTTPRequestHandler):
        server_version = "ImageGallery/1.0"

        def do_GET(self) -> None:  # noqa: N802 (HTTP method name)
            parsed = urlparse(self.path)
            if parsed.path == "/":
                return self._serve_app(parsed)
            if parsed.path == "/media":
                return self._handle_media(parsed)
            if parsed.path == "/media/campaign":
                return self._handle_campaign_media(parsed)
            if parsed.path == "/selected":
                return self._handle_selected(parsed)
            if parsed.path.startswith("/api/"):
                return self._handle_api(parsed)
            self._not_found()

        def do_POST(self) -> None:  # noqa: N802
            if self.path == "/select":
                return self._handle_select(redirect=True)
            if self.path == "/api/select":
                return self._handle_select(redirect=False)
            if self.path == "/api/register":
                return self._handle_register()
            parsed = urlparse(self.path)
            parts = [segment for segment in parsed.path.strip("/").split("/") if segment]
            if (
                len(parts) == 4
                and parts[0] == "api"
                and parts[1] == "campaigns"
                and parts[3] == "review"
            ):
                campaign_id = unquote(parts[2])
                params = parse_qs(parsed.query)
                project_id = params.get("project", [None])[0]
                return self._handle_api_campaign_review(project_id, campaign_id)
            self._not_found()

        def do_DELETE(self) -> None:  # noqa: N802
            parsed = urlparse(self.path)
            parts = [segment for segment in parsed.path.strip("/").split("/") if segment]
            if len(parts) == 3 and parts[0] == "api" and parts[1] == "slots":
                params = parse_qs(parsed.query)
                project_id = params.get("project", [None])[0]
                slot = unquote(parts[2])
                return self._handle_api_slot_delete(project_id, slot)
            self._not_found()

        def _handle_media(self, parsed) -> None:
            params = parse_qs(parsed.query)
            project_id = params.get("project", [None])[0]
            slot = params.get("slot", [None])[0]
            session_id = params.get("session", [None])[0]
            filename = params.get("file", [None])[0]
            if not slot or not session_id or not filename:
                return self._not_found()
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            try:
                ctx = context.manager.create_context(slot, session_id)
            except (ValueError, InvalidPathError):
                return self._not_found()
            manifest_path = ctx.manifest_path
            if not manifest_path.exists():
                return self._not_found()
            manifest = context.manager.read_manifest(ctx)
            allowed = {image.filename for image in manifest.images}
            allowed.update({image.raw_filename for image in manifest.images if image.raw_filename})
            if filename not in allowed:
                return self._not_found()
            file_path = ctx.session_dir / filename
            if not file_path.exists():
                return self._not_found()
            content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
            with file_path.open("rb") as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle_campaign_media(self, parsed) -> None:
            params = parse_qs(parsed.query)
            project_id = params.get("project", [None])[0]
            campaign_id = params.get("campaign", [None])[0]
            rel_path = params.get("path", [None])[0]
            if not campaign_id or not rel_path:
                return self._not_found()
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            workspace = CampaignWorkspace(context.paths, campaign_id)
            target = (workspace.root / rel_path).resolve()
            try:
                target.relative_to(workspace.root)
            except ValueError:
                return self._not_found()
            if not target.exists() or not target.is_file():
                return self._not_found()
            content_type = mimetypes.guess_type(str(target))[0] or "application/octet-stream"
            with target.open("rb") as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle_selected(self, parsed) -> None:
            params = parse_qs(parsed.query)
            project_id = params.get("project", [None])[0]
            slot = params.get("slot", [None])[0]
            if slot is None:
                return self._bad_request("Missing slot")
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            try:
                target_path = context.paths.target_for_slot(slot)
            except (ValueError, InvalidPathError):
                return self._not_found()
            if not target_path.exists():
                return self._not_found()
            content_type = mimetypes.guess_type(str(target_path))[0] or "application/octet-stream"
            with target_path.open("rb") as fh:
                data = fh.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _handle_select(self, redirect: bool) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            params = parse_qs(body)
            project_id = params.get("project", [None])[0]
            slot = params.get("slot", [None])[0]
            session_id = params.get("session", [None])[0]
            index_raw = params.get("index", [None])[0]
            if slot is None or session_id is None or index_raw is None:
                return self._bad_request("Missing parameters")
            try:
                index = int(index_raw)
            except ValueError:
                return self._bad_request("Invalid index")
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            try:
                ctx = context.manager.create_context(slot, session_id)
            except (ValueError, InvalidPathError):
                return self._not_found()
            if not ctx.manifest_path.exists():
                return self._not_found()
            manifest = context.manager.read_manifest(ctx)
            if index < 0 or index >= len(manifest.images):
                return self._bad_request("Index out of range")
            context.manager.promote_variant(ctx, manifest, index)
            if redirect:
                redirect_to = "/"
                self.send_response(303)
                self.send_header("Location", redirect_to)
                self.end_headers()
                return
            response = {
                "ok": True,
                "projectId": context.info.project_id,
                "slot": slot,
                "sessionId": session_id,
                "selectedIndex": index,
            }
            self._write_json(response)

        def _handle_api(self, parsed) -> None:
            parts = [segment for segment in parsed.path.strip("/").split("/") if segment]
            if len(parts) == 1 and parts[0] == "api":
                return self._write_json({"ok": True})
            if len(parts) == 2 and parts[0] == "api" and parts[1] == "projects":
                return self._handle_api_projects()
            if len(parts) >= 2 and parts[0] == "api" and parts[1] == "campaigns":
                params = parse_qs(parsed.query)
                project_id = params.get("project", [None])[0]
                if len(parts) == 2:
                    return self._handle_api_campaigns(project_id)
                campaign_id = unquote(parts[2])
                if len(parts) == 3:
                    return self._handle_api_campaign_detail(project_id, campaign_id)
                if len(parts) == 5 and parts[3] == "placements":
                    placement_id = unquote(parts[4])
                    return self._handle_api_campaign_placement(
                        project_id,
                        campaign_id,
                        placement_id,
                        params,
                    )
            if len(parts) >= 2 and parts[0] == "api" and parts[1] == "slots":
                params = parse_qs(parsed.query)
                project_id = params.get("project", [None])[0]
                if len(parts) == 2:
                    return self._handle_api_slots(project_id)
                slot = unquote(parts[2])
                if len(parts) == 3:
                    return self._handle_api_slot(project_id, slot)
                if len(parts) == 4 and parts[3] == "sessions":
                    return self._handle_api_slot_sessions(project_id, slot)
                if len(parts) == 5 and parts[3] == "sessions":
                    session_id = unquote(parts[4])
                    return self._handle_api_session_detail(project_id, slot, session_id)
            self._not_found()

        def _handle_api_projects(self) -> None:
            projects = []
            for info in registry.list_projects():
                projects.append(
                    {
                        "projectId": info.project_id,
                        "projectName": info.project_name,
                        "projectRoot": str(info.project_root),
                        "targetRoot": info.target_root,
                    }
                )
            default_info = registry.default_project()
            self._write_json(
                {
                    "projects": projects,
                    "defaultProjectId": default_info.project_id,
                }
            )

        def _handle_api_campaigns(self, project_id: Optional[str]) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            items: List[Dict[str, object]] = []
            for workspace in _iter_campaign_workspaces(context.paths):
                summary = _build_campaign_summary(workspace, context.info.project_id)
                if summary:
                    items.append(summary)
            items.sort(key=lambda item: (item.get("name") or item.get("campaignId") or "").lower())
            self._write_json(
                {
                    "projectId": context.info.project_id,
                    "projectName": context.info.project_name,
                    "campaigns": items,
                }
            )

        def _handle_api_campaign_detail(self, project_id: Optional[str], campaign_id: str) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            workspace = CampaignWorkspace(context.paths, campaign_id)
            if not workspace.config_path.exists():
                return self._not_found()
            detail = _build_campaign_detail(workspace, context.info.project_id)
            if not detail:
                return self._not_found()
            self._augment_campaign_detail(detail, context, workspace)
            self._write_json(detail)

        def _handle_api_campaign_placement(
            self,
            project_id: Optional[str],
            campaign_id: str,
            placement_id: str,
            params: Dict[str, List[str]],
        ) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            workspace = CampaignWorkspace(context.paths, campaign_id)
            if not workspace.config_path.exists():
                return self._not_found()
            manifests = _collect_manifests(workspace)
            manifest = manifests.get(placement_id)
            if manifest is None:
                return self._not_found()
            state_filter = params.get("state", [None])[0]
            allowed_state = _as_review_state(state_filter) if state_filter else None
            variants: List[Dict[str, object]] = []
            for route_entry in manifest.routes:
                for variant in route_entry.variants:
                    state_key = _as_review_state(variant.review_state)
                    if allowed_state and state_key != allowed_state:
                        continue
                    variant_payload = {
                        "variantId": variant.variant_id,
                        "index": variant.index,
                        "file": variant.file,
                        "thumbnail": variant.thumbnail,
                        "reviewState": state_key,
                        "seed": variant.seed,
                        "prompt": variant.prompt,
                        "notes": variant.review_notes,
                        "createdAt": variant.created_at,
                        "placementId": placement_id,
                        "routeId": route_entry.route_id,
                    }
                    variants.append(variant_payload)
            placement_counts = _placement_state_counts(manifest)
            response = {
                "placementId": placement_id,
                "campaignId": campaign_id,
                "variants": variants,
                "counts": placement_counts,
                "updatedAt": manifest.updated_at,
            }
            self._augment_campaign_variants(response["variants"], context, workspace)
            self._write_json(response)

        def _handle_api_campaign_review(self, project_id: Optional[str], campaign_id: str) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            workspace = CampaignWorkspace(context.paths, campaign_id)
            if not workspace.config_path.exists():
                return self._not_found()

            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b"{}"
            try:
                payload = json.loads(raw.decode("utf-8"))
            except json.JSONDecodeError:
                return self._bad_request("Invalid JSON payload")

            placement_id = payload.get("placementId") or payload.get("placement_id")
            route_id = payload.get("routeId") or payload.get("route_id")
            variant_index = payload.get("variantIndex") or payload.get("variant_index")
            state_value = payload.get("state")
            notes = payload.get("notes")

            if placement_id is None or route_id is None or variant_index is None or state_value is None:
                return self._bad_request("Missing required fields")

            try:
                variant_index = int(variant_index)
            except (TypeError, ValueError):
                return self._bad_request("variantIndex must be an integer")

            try:
                new_state = ReviewState(state_value)
            except ValueError:
                return self._bad_request("Invalid review state")

            manifests = _collect_manifests(workspace)
            manifest = manifests.get(placement_id)
            if manifest is None:
                return self._not_found()

            target_variant = None
            for route_entry in manifest.routes:
                if route_entry.route_id != route_id:
                    continue
                for variant in route_entry.variants:
                    if variant.index == variant_index:
                        target_variant = variant
                        break
                if target_variant:
                    break

            if target_variant is None:
                return self._not_found()

            target_variant.review_state = new_state
            if notes is not None:
                target_variant.review_notes = notes or None
            manifest.updated_at = format_ts(datetime.utcnow())

            workspace.save_manifest(manifest)

            placement_counts = _placement_state_counts(manifest)
            all_manifests = _collect_manifests(workspace)
            totals: Dict[str, int] = {state.value: 0 for state in ReviewState}
            total_variants = 0
            for item in all_manifests.values():
                counts = _placement_state_counts(item)
                for key, value in counts.items():
                    totals[key] = totals.get(key, 0) + value
                    total_variants += value

            variant_payload = {
                "variantId": target_variant.variant_id,
                "index": target_variant.index,
                "file": target_variant.file,
                "thumbnail": target_variant.thumbnail,
                "reviewState": new_state.value,
                "seed": target_variant.seed,
                "prompt": target_variant.prompt,
                "notes": target_variant.review_notes,
                "createdAt": target_variant.created_at,
                "placementId": placement_id,
                "routeId": route_id,
            }

            self._augment_campaign_variants([variant_payload], context, workspace)

            response = {
                "ok": True,
                "campaignId": campaign_id,
                "placementId": placement_id,
                "routeId": route_id,
                "counts": placement_counts,
                "stats": {
                    "total": total_variants,
                    "approved": totals.get(ReviewState.APPROVED.value, 0),
                    "pending": totals.get(ReviewState.PENDING.value, 0),
                    "revise": totals.get(ReviewState.REVISE.value, 0),
                },
                "variant": variant_payload,
            }
            self._write_json(response)

        def _handle_api_slots(self, project_id: Optional[str]) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            summaries = build_slot_index(context.paths)
            items = []
            for slot, summary in sorted(summaries.items()):
                last_updated = summary.last_updated
                items.append(
                    {
                        "slot": slot,
                        "sessionCount": summary.session_count,
                        "selectedPath": summary.selected_path,
                        "selectedIndex": summary.selected_index,
                        "lastUpdated": format_ts(last_updated) if last_updated else None,
                        "warningCount": len(summary.warnings),
                        "selectedImageUrl": self._selected_image_url(context.info.project_id, slot),
                    }
                )
            self._write_json(
                {
                    "projectId": context.info.project_id,
                    "projectName": context.info.project_name,
                    "slots": items,
                }
            )

        def _handle_api_slot(self, project_id: Optional[str], slot: str) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            try:
                manifests = list_manifests_for_slot(context.paths, slot)
            except (ValueError, InvalidPathError):
                return self._not_found()
            manifests.sort(key=lambda m: m.completed_at, reverse=True)
            summaries = [self._summarize_session(context, manifest) for manifest in manifests]
            variants: List[Dict[str, object]] = []
            slot_selected_hash = None
            current_selection = None
            if manifests:
                latest_manifest = manifests[0]
                if latest_manifest.images:
                    selected_index = latest_manifest.selected_index
                    if 0 <= selected_index < len(latest_manifest.images):
                        selected_image = latest_manifest.images[selected_index]
                        slot_selected_hash = selected_image.sha256
                        current_selection = {
                            "projectId": context.info.project_id,
                            "projectName": context.info.project_name,
                            "slot": latest_manifest.slot,
                            "sessionId": latest_manifest.session_id,
                            "variantIndex": selected_index,
                            "completedAt": format_ts(latest_manifest.completed_at),
                            "processed": {
                                "url": self._variant_media_url(
                                    context.info.project_id,
                                    latest_manifest.slot,
                                    latest_manifest.session_id,
                                    selected_image.filename,
                                ),
                                "filename": selected_image.filename,
                                "width": selected_image.width,
                                "height": selected_image.height,
                                "mediaType": selected_image.media_type,
                            },
                            "raw": (
                                {
                                    "url": self._variant_media_url(
                                        context.info.project_id,
                                        latest_manifest.slot,
                                        latest_manifest.session_id,
                                        selected_image.raw_filename,
                                    ),
                                    "filename": selected_image.raw_filename,
                                }
                                if selected_image.raw_filename
                                else None
                            ),
                            "slotImageUrl": self._selected_image_url(context.info.project_id, latest_manifest.slot),
                        }
            for manifest in manifests:
                variants.extend(self._map_manifest_variants(context, manifest, slot_selected_hash))
            variants.sort(key=lambda item: item["capturedAt"], reverse=True)
            self._write_json(
                {
                    "projectId": context.info.project_id,
                    "projectName": context.info.project_name,
                    "slot": slot,
                    "sessions": summaries,
                    "variants": variants,
                    "currentSelection": current_selection,
                }
            )

        def _handle_api_slot_delete(self, project_id: Optional[str], slot: Optional[str]) -> None:
            if not slot:
                return self._bad_request("Missing slot")
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            try:
                result = delete_slot(context.paths, slot)
            except (ValueError, InvalidPathError):
                return self._not_found()
            response = {
                "ok": True,
                "projectId": context.info.project_id,
                "slot": result.slot,
                "removedSessions": result.removed_sessions,
                "removedTargets": result.removed_targets,
            }
            self._write_json(response)

        def _handle_api_slot_sessions(self, project_id: Optional[str], slot: str) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            try:
                manifests = list_manifests_for_slot(context.paths, slot)
            except (ValueError, InvalidPathError):
                return self._not_found()
            manifests.sort(key=lambda m: m.completed_at, reverse=True)
            summaries = [self._summarize_session(context, manifest) for manifest in manifests]
            variants: List[Dict[str, object]] = []
            slot_selected_hash = None
            current_selection = None
            if manifests:
                latest_manifest = manifests[0]
                if latest_manifest.images:
                    selected_index = latest_manifest.selected_index
                    if 0 <= selected_index < len(latest_manifest.images):
                        selected_image = latest_manifest.images[selected_index]
                        slot_selected_hash = selected_image.sha256
                        current_selection = {
                            "projectId": context.info.project_id,
                            "projectName": context.info.project_name,
                            "slot": latest_manifest.slot,
                            "sessionId": latest_manifest.session_id,
                            "variantIndex": selected_index,
                            "completedAt": format_ts(latest_manifest.completed_at),
                            "processed": {
                                "url": self._variant_media_url(
                                    context.info.project_id,
                                    latest_manifest.slot,
                                    latest_manifest.session_id,
                                    selected_image.filename,
                                ),
                                "filename": selected_image.filename,
                                "width": selected_image.width,
                                "height": selected_image.height,
                                "mediaType": selected_image.media_type,
                            },
                            "raw": (
                                {
                                    "url": self._variant_media_url(
                                        context.info.project_id,
                                        latest_manifest.slot,
                                        latest_manifest.session_id,
                                        selected_image.raw_filename,
                                    ),
                                    "filename": selected_image.raw_filename,
                                }
                                if selected_image.raw_filename
                                else None
                            ),
                            "slotImageUrl": self._selected_image_url(context.info.project_id, latest_manifest.slot),
                        }
            for manifest in manifests:
                variants.extend(self._map_manifest_variants(context, manifest, slot_selected_hash))
            variants.sort(key=lambda item: item["capturedAt"], reverse=True)
            self._write_json(
                {
                    "projectId": context.info.project_id,
                    "projectName": context.info.project_name,
                    "slot": slot,
                    "sessions": summaries,
                    "variants": variants,
                    "currentSelection": current_selection,
                }
            )

        def _handle_api_session_detail(self, project_id: Optional[str], slot: str, session_id: str) -> None:
            context = self._get_context(project_id)
            if context is None:
                return self._not_found()
            ctx, manifest = self._resolve_session(context, slot, session_id)
            if manifest is None or ctx is None:
                return self._not_found()
            detail = manifest.to_dict()
            variants = []
            for index, image in enumerate(manifest.images):
                processed_url = self._variant_media_url(context.info.project_id, manifest.slot, session_id, image.filename)
                raw_url = None
                if image.raw_filename:
                    raw_url = self._variant_media_url(context.info.project_id, manifest.slot, session_id, image.raw_filename)
                variants.append(
                    {
                        "index": index,
                        "selected": index == manifest.selected_index,
                        "processed": {
                            "url": processed_url,
                            "filename": image.filename,
                            "width": image.width,
                            "height": image.height,
                            "mediaType": image.media_type,
                        },
                        "raw": {
                            "url": raw_url,
                            "filename": image.raw_filename,
                        }
                        if raw_url
                        else None,
                        "sha256": image.sha256,
                        "original": {
                            "width": image.original_width,
                            "height": image.original_height,
                        },
                        "cropFraction": image.crop_fraction,
                    }
                )
            detail["variants"] = variants
            detail["projectId"] = context.info.project_id
            detail["projectName"] = context.info.project_name
            self._write_json(detail)
        def _find_session_dir(self, session_id: str):
            root = paths.sessions_root
            if not root.exists():
                return None
            for candidate in root.glob(f"*_{session_id}"):
                if candidate.is_dir():
                    return candidate
            return None

        def _serve_app(self, parsed=None) -> None:
            body = _app_html()
            self._write_html(body)

        def _write_html(self, body: str) -> None:
            data = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _write_json(self, payload) -> None:
            data = json.dumps(payload).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _get_context(self, project_id: Optional[str]) -> Optional[ProjectContext]:
            try:
                return registry.get_context(project_id)
            except KeyError:
                return None

        def _selected_image_url(self, project_id: str, slot: str) -> str:
            params = {
                "project": project_id,
                "slot": slot,
            }
            encoded = "&".join(f"{quote(str(key))}={quote(str(value))}" for key, value in params.items())
            return f"/selected?{encoded}"

        def _variant_media_url(
            self,
            project_id: str,
            slot: str,
            session_id: str,
            filename: str,
        ) -> str:
            params = {
                "project": project_id,
                "slot": slot,
                "session": session_id,
                "file": filename,
            }
            encoded = "&".join(f"{quote(str(key))}={quote(str(value))}" for key, value in params.items())
            return f"/media?{encoded}"

        def _campaign_media_url(
            self,
            project_id: str,
            campaign_id: str,
            relative_path: str,
        ) -> str:
            params = {
                "project": project_id,
                "campaign": campaign_id,
                "path": relative_path,
            }
            encoded = "&".join(f"{quote(str(key))}={quote(str(value))}" for key, value in params.items())
            return f"/media/campaign?{encoded}"

        def _augment_campaign_variants(
            self,
            variants: Iterable[Dict[str, object]],
            context: ProjectContext,
            workspace: CampaignWorkspace,
        ) -> None:
            for variant in variants:
                thumb_rel = variant.get("thumbnail")
                file_rel = variant.get("file")
                campaign_id = workspace.campaign_id
                if thumb_rel:
                    thumb_path = (workspace.root / thumb_rel).resolve()
                    try:
                        thumb_path.relative_to(workspace.root)
                    except ValueError:
                        variant["thumbnailUrl"] = None
                    else:
                        if thumb_path.exists():
                            variant["thumbnailUrl"] = self._campaign_media_url(
                                context.info.project_id,
                                campaign_id,
                                thumb_rel,
                            )
                        else:
                            variant["thumbnailUrl"] = None
                else:
                    variant["thumbnailUrl"] = None

                if file_rel:
                    file_path = (workspace.root / file_rel).resolve()
                    try:
                        file_path.relative_to(workspace.root)
                    except ValueError:
                        variant["imageUrl"] = None
                    else:
                        if file_path.exists():
                            variant["imageUrl"] = self._campaign_media_url(
                                context.info.project_id,
                                campaign_id,
                                file_rel,
                            )
                        else:
                            variant["imageUrl"] = None
                else:
                    variant["imageUrl"] = None

        def _augment_campaign_detail(
            self,
            detail: Dict[str, object],
            context: ProjectContext,
            workspace: CampaignWorkspace,
        ) -> None:
            matrix = detail.get("matrix", [])
            for cell in matrix:
                variants = cell.get("variants", [])
                self._augment_campaign_variants(variants, context, workspace)
            placements = detail.get("placements", [])
            for placement in placements:
                updated_at = placement.get("updatedAt")
                placement["updatedAt"] = updated_at
            exports = detail.get("exports", [])
            for entry in exports:
                generated_at = entry.get("generatedAt")
                entry["generatedAt"] = generated_at

        def _resolve_session(
            self,
            context: ProjectContext,
            slot: str,
            session_id: str,
        ) -> tuple[Optional[object], Optional[object]]:
            try:
                ctx = context.manager.create_context(slot, session_id)
            except (ValueError, InvalidPathError):
                return None, None
            if not ctx.manifest_path.exists():
                return None, None
            try:
                manifest = context.manager.read_manifest(ctx)
            except FileNotFoundError:
                return None, None
            return ctx, manifest

        def _summarize_session(self, context: ProjectContext, manifest) -> Dict[str, object]:
            summary: Dict[str, object] = {
                "projectId": context.info.project_id,
                "projectName": context.info.project_name,
                "slot": manifest.slot,
                "sessionId": manifest.session_id,
                "completedAt": format_ts(manifest.completed_at),
                "createdAt": format_ts(manifest.created_at),
                "variantCount": len(manifest.images),
                "selectedIndex": manifest.selected_index,
                "selectedPath": manifest.selected_path,
                "warnings": list(manifest.warnings),
                "provider": manifest.effective.provider,
                "model": manifest.effective.model,
                "size": manifest.effective.size or manifest.effective.aspect_ratio,
                "prompt": manifest.effective.prompt,
                "requestText": manifest.request.request_text,
            }
            return summary

        def _map_manifest_variants(
            self,
            context: ProjectContext,
            manifest,
            slot_selected_hash: Optional[str],
        ) -> List[Dict[str, object]]:
            results: List[Dict[str, object]] = []
            session_selected_hash: Optional[str] = None
            if 0 <= manifest.selected_index < len(manifest.images):
                session_selected_hash = manifest.images[manifest.selected_index].sha256
            for index, image in enumerate(manifest.images):
                processed = {
                    "url": self._variant_media_url(
                        context.info.project_id,
                        manifest.slot,
                        manifest.session_id,
                        image.filename,
                    ),
                    "filename": image.filename,
                    "width": image.width,
                    "height": image.height,
                    "mediaType": image.media_type,
                }
                raw = None
                if image.raw_filename:
                    raw = {
                        "url": self._variant_media_url(
                            context.info.project_id,
                            manifest.slot,
                            manifest.session_id,
                            image.raw_filename,
                        ),
                        "filename": image.raw_filename,
                    }
                results.append(
                    {
                        "projectId": context.info.project_id,
                        "projectName": context.info.project_name,
                        "slot": manifest.slot,
                        "sessionId": manifest.session_id,
                        "variantIndex": index,
                        "processed": processed,
                        "raw": raw,
                        "sessionWarnings": list(manifest.warnings),
                        "sessionProvider": manifest.effective.provider,
                        "sessionModel": manifest.effective.model,
                        "sessionSize": manifest.effective.size or manifest.effective.aspect_ratio,
                        "sessionPrompt": manifest.effective.prompt,
                        "sessionRequest": manifest.request.request_text,
                        "sessionCompletedAt": format_ts(manifest.completed_at),
                        "sessionCreatedAt": format_ts(manifest.created_at),
                        "capturedAt": format_ts(manifest.completed_at),
                        "isSessionSelected": session_selected_hash is not None
                        and image.sha256 == session_selected_hash,
                        "isSlotSelected": slot_selected_hash is not None
                        and image.sha256 == slot_selected_hash,
                        "sha256": image.sha256,
                        "cropFraction": image.crop_fraction,
                        "original": {
                            "width": image.original_width,
                            "height": image.original_height,
                        },
                    }
                )
            return results

        def _not_found(self) -> None:
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Not Found")

        def _bad_request(self, message: str) -> None:
            data = message.encode("utf-8")
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args) -> None:  # noqa: A003 - match BaseHTTPRequestHandler signature
            return  # Silence default logging to keep CLI output clean

    return Handler
def _app_html() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>ImageMCP Gallery</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {
      color-scheme: dark;
      --bg: #0b0b0f;
      --bg-surface: #15151a;
      --bg-panel: #1f1f28;
      --accent: #38bdf8;
      --accent-soft: rgba(56, 189, 248, 0.16);
      --accent-strong: rgba(56, 189, 248, 0.32);
      --text: #f5f5f5;
      --text-soft: #cbd5f5;
      --border: rgba(148, 163, 184, 0.18);
      --warning: #f97316;
      --warning-soft: rgba(249, 115, 22, 0.2);
      font-family: "Inter", "SF Pro Text", "Segoe UI", system-ui, sans-serif;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: linear-gradient(160deg, #0b0b0f 0%, #11111a 40%, #060608 100%);
      color: var(--text);
    }

    a { color: var(--accent); text-decoration: none; }

    #app { min-height: 100vh; display: flex; flex-direction: column; }

    .top-bar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1rem 1.5rem;
      background: rgba(12, 12, 20, 0.75);
      backdrop-filter: blur(14px);
      border-bottom: 1px solid var(--border);
      position: sticky;
      top: 0;
      z-index: 20;
    }

    .brand-group {
      display: flex;
      align-items: center;
      gap: 1.25rem;
    }

    .brand {
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      font-size: 0.9rem;
      color: var(--text-soft);
    }

    .view-tabs {
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.2rem;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.12);
      border: 1px solid rgba(148, 163, 184, 0.18);
    }

    .view-tabs .ghost-button {
      padding: 0.3rem 0.75rem;
      font-size: 0.78rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .view-tabs .ghost-button[data-active="true"] {
      background: var(--accent-soft);
      border-color: var(--accent);
      color: var(--accent);
      box-shadow: 0 10px 24px rgba(56, 189, 248, 0.22);
    }

    .project-switcher {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.35rem 0.55rem;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.12);
      border: 1px solid rgba(148, 163, 184, 0.18);
      font-size: 0.8rem;
    }

    .project-switcher label {
      font-weight: 600;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: var(--text-soft);
    }

    .project-switcher select {
      background: transparent;
      border: none;
      color: var(--text);
      font-size: 0.85rem;
      font-weight: 600;
      outline: none;
      appearance: none;
      padding-right: 1.4rem;
      position: relative;
      cursor: pointer;
    }

    .project-switcher select option {
      color: #0f172a;
    }

    .view-actions,
    .top-actions {
      display: flex;
      gap: 0.75rem;
      align-items: center;
    }

    main {
      flex: 1;
      padding: 1.5rem;
      max-width: 1280px;
      width: 100%;
      margin: 0 auto;
    }

    .view {
      display: none;
      flex-direction: column;
      gap: 1rem;
    }

    .view.active { display: flex; }

    .view-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .view-header h1 {
      font-size: 1.6rem;
      margin: 0;
    }

    .view-subtitle {
      display: inline-block;
      margin-top: 0.35rem;
      font-size: 0.85rem;
      color: var(--text-soft);
      letter-spacing: 0.04em;
      text-transform: uppercase;
    }

    .slot-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
      gap: 1.25rem;
    }

    .input-control {
      padding: 0.4rem 0.65rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: rgba(12, 12, 20, 0.6);
      color: var(--text);
      font-size: 0.9rem;
      outline: none;
    }

    .input-control:focus {
      border-color: var(--accent);
      box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.4);
    }

    .campaign-dashboard {
      display: grid;
      grid-template-columns: minmax(0, 1fr) 320px;
      gap: 1.5rem;
      align-items: start;
    }

    .campaign-summary-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1rem;
    }

    .campaign-card {
      border-radius: 16px;
      border: 1px solid var(--border);
      background: rgba(15, 18, 30, 0.75);
      padding: 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      transition: border-color 0.18s ease, box-shadow 0.18s ease;
      position: relative;
    }

    .campaign-card:hover {
      border-color: var(--accent);
      box-shadow: 0 12px 28px rgba(14, 165, 233, 0.18);
    }

    .campaign-card[data-active="true"] {
      border-color: var(--accent);
      box-shadow: 0 16px 34px rgba(14, 165, 233, 0.28);
    }

    .campaign-card-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .campaign-card-title {
      margin: 0;
      font-size: 1.05rem;
      font-weight: 600;
    }

    .campaign-card-meta,
    .campaign-card-stats {
      display: flex;
      gap: 0.6rem;
      flex-wrap: wrap;
      font-size: 0.78rem;
      color: var(--text-soft);
    }

    .campaign-progress-bar {
      position: relative;
      height: 8px;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.16);
      overflow: hidden;
    }

    .campaign-progress-bar span {
      position: absolute;
      inset: 0;
      border-radius: 999px;
      background: linear-gradient(90deg, rgba(56, 189, 248, 0.9), rgba(96, 165, 250, 0.9));
      transition: width 0.28s ease;
    }

    .campaign-card-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .campaign-dashboard-side {
      display: flex;
      flex-direction: column;
      gap: 1rem;
      position: sticky;
      top: 92px;
    }

    .panel {
      border-radius: 16px;
      border: 1px solid var(--border);
      background: rgba(15, 18, 30, 0.78);
      padding: 1rem 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.5rem;
    }

    .panel-header h2 {
      margin: 0;
      font-size: 0.95rem;
      letter-spacing: 0.04em;
      text-transform: uppercase;
      color: rgba(203, 213, 225, 0.82);
    }

    .metric-list,
    .alert-list,
    .action-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      font-size: 0.85rem;
    }

    .metric-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--text-soft);
    }

    .metric-item strong {
      color: var(--text);
      font-weight: 600;
    }

    .alert-item {
      border-radius: 12px;
      border: 1px solid rgba(249, 115, 22, 0.35);
      background: rgba(249, 115, 22, 0.12);
      padding: 0.6rem 0.75rem;
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .action-list button {
      width: 100%;
      justify-content: flex-start;
    }

    .campaign-detail-layout {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      gap: 1.5rem;
      align-items: start;
    }

    .campaign-summary-column {
      position: sticky;
      top: 92px;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .campaign-main-panel {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .alert-banner {
      border-radius: 12px;
      border: 1px solid rgba(249, 115, 22, 0.35);
      background: rgba(249, 115, 22, 0.12);
      padding: 0.85rem 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }

    .filter-group {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      font-size: 0.82rem;
      color: var(--text-soft);
    }

    .filter-group label {
      display: flex;
      flex-direction: column;
      gap: 0.2rem;
    }

    .filter-group select {
      padding: 0.35rem 0.6rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: rgba(12, 12, 20, 0.6);
      color: var(--text);
    }

    .progress-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .progress-item {
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
      font-size: 0.82rem;
      color: var(--text-soft);
    }

    .progress-item-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .campaign-matrix-grid {
      display: grid;
      gap: 1rem;
    }

    .review-mode-selection {
      display: flex;
      flex-wrap: wrap;
      gap: 1rem;
      margin-bottom: 1.25rem;
    }

    .review-mode-card {
      flex: 1 1 260px;
      border-radius: 16px;
      border: 1px solid rgba(148, 163, 184, 0.22);
      background: rgba(12, 12, 20, 0.5);
      padding: 1rem 1.25rem;
      text-align: left;
      color: inherit;
      cursor: pointer;
      transition: transform 0.18s ease, border 0.18s ease, box-shadow 0.18s ease;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }

    .review-mode-card:hover,
    .review-mode-card:focus {
      outline: none;
      transform: translateY(-3px);
      border-color: var(--accent);
      box-shadow: 0 14px 32px rgba(14, 165, 233, 0.2);
    }

    .review-mode-card h3 {
      margin: 0;
      font-size: 1.05rem;
      font-weight: 600;
    }

    .review-mode-card p {
      margin: 0;
      font-size: 0.85rem;
      color: var(--text-soft);
      line-height: 1.5;
    }

    .campaign-matrix-card {
      border-radius: 16px;
      border: 1px solid var(--border);
      background: rgba(15, 18, 30, 0.72);
      padding: 1rem 1.1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .campaign-matrix-card header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.75rem;
    }

    .campaign-variant-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
      gap: 0.5rem;
    }

    .campaign-variant-thumb {
      display: block;
      border-radius: 10px;
      overflow: hidden;
      border: 1px solid rgba(148, 163, 184, 0.22);
      background: rgba(12, 12, 20, 0.4);
      height: 90px;
      position: relative;
    }

    .campaign-variant-thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .focus-overlay-card {
      width: min(1000px, 94vw);
      max-height: 92vh;
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .focus-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }

    .focus-context {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
    }

    .focus-context h2 {
      margin: 0;
      font-size: 1.1rem;
    }

    .focus-hero {
      flex: 1 1 auto;
      min-height: 360px;
      border-radius: 16px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      background: radial-gradient(circle at center, rgba(148, 163, 184, 0.12), rgba(15, 18, 30, 0.75));
      display: flex;
      align-items: center;
      justify-content: center;
      overflow: hidden;
      position: relative;
    }

    .focus-hero img {
      max-width: 100%;
      max-height: 100%;
      object-fit: contain;
    }

    .focus-hero-placeholder {
      font-size: 1rem;
      color: var(--text-soft);
      text-align: center;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .focus-strip-wrapper {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
    }

    .focus-strip {
      display: flex;
      gap: 0.6rem;
      overflow-x: auto;
      padding-bottom: 0.25rem;
    }

    .focus-thumb {
      flex: 0 0 auto;
      width: 120px;
      height: 90px;
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.25);
      overflow: hidden;
      position: relative;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(12, 12, 20, 0.5);
      transition: border 0.18s ease, transform 0.18s ease;
    }

    .focus-thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .focus-thumb[data-selected="true"] {
      border-color: var(--accent);
      box-shadow: 0 8px 22px rgba(14, 165, 233, 0.25);
      transform: translateY(-4px);
    }

    .focus-thumb .status-chip {
      position: absolute;
      bottom: 6px;
      left: 6px;
      font-size: 0.65rem;
      padding: 0.15rem 0.45rem;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.72);
      color: var(--text);
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .focus-thumb[data-state="approved"] .status-chip {
      background: rgba(34, 197, 94, 0.28);
      color: #4ade80;
    }

    .focus-thumb[data-state="revise"] .status-chip {
      background: rgba(249, 115, 22, 0.28);
      color: #fb923c;
    }

    .focus-thumb[data-kind="next"] {
      border-style: dashed;
      color: var(--text-soft);
      font-size: 0.8rem;
      letter-spacing: 0.08em;
    }

    .focus-actions {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
    }

    .focus-actions-left {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      color: var(--text-soft);
      font-size: 0.82rem;
    }

    .focus-notes {
      display: none;
      flex-direction: column;
      gap: 0.4rem;
      margin-top: 0.75rem;
    }

    .focus-notes textarea {
      width: 100%;
      min-height: 100px;
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.28);
      background: rgba(12, 12, 20, 0.6);
      padding: 0.6rem 0.75rem;
      color: var(--text);
      font-size: 0.9rem;
      resize: vertical;
    }

    .focus-notes[data-visible="true"] {
      display: flex;
    }

    .blitz-overlay-card {
      width: min(1100px, 96vw);
      max-height: 94vh;
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }

    .blitz-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 1rem;
    }

    .blitz-summary {
      display: flex;
      gap: 1.25rem;
      font-size: 0.88rem;
      color: var(--text-soft);
    }

    .blitz-content {
      flex: 1 1 auto;
      overflow-y: auto;
      padding-right: 0.35rem;
      display: flex;
      flex-direction: column;
      gap: 2rem;
    }

    .blitz-placement {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .blitz-placement header {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 0.75rem;
    }

    .blitz-placement h3 {
      margin: 0;
      font-size: 1rem;
    }

    .blitz-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 0.8rem;
    }

    .blitz-tile {
      position: relative;
      border-radius: 14px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      overflow: hidden;
      cursor: pointer;
      background: rgba(12, 12, 20, 0.55);
      transition: border 0.18s ease, transform 0.18s ease;
      min-height: 160px;
      display: flex;
      align-items: center;
      justify-content: center;
    }

    .blitz-tile img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .blitz-tile[data-state="approved"] {
      border-color: rgba(34, 197, 94, 0.55);
      box-shadow: 0 10px 24px rgba(34, 197, 94, 0.28);
    }

    .blitz-tile[data-state="revise"] {
      border-color: rgba(249, 115, 22, 0.55);
      box-shadow: 0 10px 24px rgba(249, 115, 22, 0.26);
    }

    .blitz-tile:focus-visible {
      outline: 2px solid var(--accent);
      outline-offset: 3px;
    }

    .blitz-tile[data-active="true"] {
      outline: 2px solid var(--accent);
      outline-offset: 3px;
    }

    .blitz-tile .tile-badge {
      position: absolute;
      top: 8px;
      left: 8px;
      background: rgba(15, 23, 42, 0.75);
      color: var(--text);
      padding: 0.18rem 0.45rem;
      border-radius: 999px;
      font-size: 0.7rem;
      letter-spacing: 0.06em;
      text-transform: uppercase;
    }

    .blitz-tile .tile-meta {
      position: absolute;
      bottom: 8px;
      left: 8px;
      right: 8px;
      display: flex;
      justify-content: space-between;
      font-size: 0.7rem;
      color: rgba(226, 232, 240, 0.86);
      text-shadow: 0 0 6px rgba(2, 6, 23, 0.85);
    }

    .blitz-empty {
      padding: 0.85rem 1rem;
      border-radius: 12px;
      border: 1px dashed rgba(148, 163, 184, 0.3);
      color: var(--text-soft);
      font-size: 0.85rem;
    }

    .campaign-chip {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      background: rgba(148, 163, 184, 0.12);
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .manifest-list,
    .campaign-route-list,
    .campaign-export-list,
    .campaign-log-list {
      display: flex;
      flex-direction: column;
      gap: 0.55rem;
      font-size: 0.82rem;
      color: var(--text-soft);
    }

    .campaign-route-card {
      border: 1px solid rgba(148, 163, 184, 0.2);
      border-radius: 10px;
      padding: 0.6rem 0.7rem;
      background: rgba(12, 12, 20, 0.48);
      cursor: pointer;
      transition: border 0.18s ease, background 0.18s ease;
    }

    .campaign-route-card[data-active="true"] {
      border-color: var(--accent);
      background: rgba(56, 189, 248, 0.16);
      box-shadow: 0 12px 28px rgba(14, 165, 233, 0.24);
    }

    .campaign-route-section {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .campaign-route-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      gap: 0.5rem;
    }

    .campaign-route-name {
      font-weight: 600;
      font-size: 0.95rem;
    }

    .campaign-variant-overlay {
      max-width: 960px;
      width: 100%;
      gap: 1rem;
    }

    .overlay-title-group {
      display: flex;
      flex-direction: column;
      gap: 0.25rem;
    }

    .overlay-subtitle {
      font-size: 0.8rem;
      color: var(--text-soft);
    }

    .campaign-overlay-controls {
      display: flex;
      gap: 1rem;
      align-items: flex-end;
      margin-bottom: 0.5rem;
    }

    .campaign-overlay-controls .control {
      display: flex;
      flex-direction: column;
      gap: 0.3rem;
      flex: 1;
      font-size: 0.82rem;
      color: var(--text-soft);
    }

    .campaign-overlay-controls select {
      padding: 0.4rem 0.6rem;
      border-radius: 8px;
      border: 1px solid var(--border);
      background: rgba(12, 12, 20, 0.6);
      color: var(--text);
    }

    .variant-compare {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 1rem;
    }

    .variant-column {
      background: rgba(12, 12, 20, 0.5);
      border: 1px solid rgba(148, 163, 184, 0.18);
      border-radius: 14px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .variant-preview {
      background: rgba(0, 0, 0, 0.35);
      display: flex;
      align-items: center;
      justify-content: center;
      min-height: 220px;
    }

    .variant-preview img {
      max-width: 100%;
      height: auto;
    }

    .variant-meta {
      padding: 0 0.75rem 0.85rem;
      font-size: 0.8rem;
      color: var(--text-soft);
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }

    .campaign-overlay-meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }

    .campaign-overlay-meta section {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      font-size: 0.82rem;
      color: var(--text-soft);
    }

    .campaign-overlay-meta h3 {
      margin: 0;
      font-size: 0.85rem;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: rgba(203, 213, 225, 0.85);
    }

    .campaign-overlay-meta textarea {
      min-height: 90px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: rgba(12, 12, 20, 0.6);
      color: var(--text);
      padding: 0.5rem 0.65rem;
      resize: vertical;
    }

    .campaign-overlay-footer {
      margin-top: 1rem;
      display: flex;
      justify-content: space-between;
      gap: 0.75rem;
      flex-wrap: wrap;
      align-items: center;
    }

    .campaign-overlay-actions-left {
      display: flex;
      gap: 0.5rem;
      flex-wrap: wrap;
    }

    .prompt-diff {
      font-family: "JetBrains Mono", "SFMono-Regular", Menlo, monospace;
      font-size: 0.75rem;
      background: rgba(10, 14, 24, 0.8);
      border-radius: 10px;
      border: 1px solid rgba(148, 163, 184, 0.2);
      padding: 0.6rem;
      line-height: 1.4;
      min-height: 80px;
    }

    .prompt-diff .diff-add {
      color: #34d399;
    }

    .prompt-diff .diff-remove {
      color: #f87171;
      text-decoration: line-through;
    }

    .timeline {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      font-size: 0.78rem;
      color: var(--text-soft);
    }

    .timeline-entry {
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }

    .alert-pill {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      padding: 0.2rem 0.55rem;
      border-radius: 999px;
      border: 1px solid rgba(249, 115, 22, 0.4);
      background: rgba(249, 115, 22, 0.18);
      font-size: 0.75rem;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .empty-note {
      font-size: 0.8rem;
      color: var(--text-soft);
    }

    .slot-card {
      background: var(--bg-panel);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      cursor: pointer;
      transition: transform 0.2s ease, border 0.2s ease, box-shadow 0.2s ease;
      position: relative;
    }

    .slot-card:hover {
      transform: translateY(-3px);
      border-color: var(--accent);
      box-shadow: 0 16px 36px rgba(15, 118, 209, 0.18);
    }

    .slot-card[data-active="true"] {
      border-color: var(--accent);
      box-shadow: 0 12px 28px rgba(14, 165, 233, 0.22);
    }

    .slot-card.has-warning {
      border-color: var(--warning-soft);
      box-shadow: 0 0 0 1px var(--warning-soft);
    }

    .thumb {
      width: 100%;
      aspect-ratio: 4 / 3;
      border-radius: 10px;
      overflow: hidden;
      background: linear-gradient(135deg, rgba(148, 163, 184, 0.08), rgba(30, 41, 59, 0.16));
      display: flex;
      align-items: center;
      justify-content: center;
      position: relative;
    }

    .thumb img {
      width: 100%;
      height: 100%;
      object-fit: cover;
    }

    .thumb-placeholder {
      font-size: 0.8rem;
      color: var(--text-soft);
      text-transform: uppercase;
      letter-spacing: 0.1em;
    }

    .slot-meta {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }

    .slot-meta h2 {
      margin: 0;
      font-size: 1rem;
      font-weight: 600;
      color: var(--text);
    }

    .slot-meta span {
      font-size: 0.85rem;
      color: var(--text-soft);
    }

    .badge {
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      padding: 0.15rem 0.45rem;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent);
      font-weight: 600;
    }

    .badge-warning {
      background: var(--warning-soft);
      color: var(--warning);
    }

    .badge-info {
      background: rgba(59, 130, 246, 0.25);
      color: #93c5fd;
    }

    .ghost-button,
    .primary-button,
    .danger-button {
      border-radius: 8px;
      border: 1px solid transparent;
      padding: 0.45rem 0.9rem;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      background: none;
      color: var(--text);
      transition: all 0.18s ease;
    }

    .ghost-button {
      border-color: rgba(148, 163, 184, 0.2);
      background: rgba(148, 163, 184, 0.08);
    }

    .ghost-button:hover {
      border-color: var(--accent);
      color: var(--accent);
    }

    .ghost-button[data-active="true"] {
      border-color: var(--accent);
      background: var(--accent-soft);
      color: var(--accent);
    }

    .primary-button {
      background: var(--accent);
      color: #020617;
      border-color: rgba(14, 165, 233, 0.4);
      box-shadow: 0 10px 30px rgba(14, 165, 233, 0.3);
    }

    .primary-button:hover {
      box-shadow: 0 18px 36px rgba(14, 165, 233, 0.35);
      transform: translateY(-1px);
    }

    .primary-button[disabled],
    .ghost-button[disabled],
    .danger-button[disabled] {
      opacity: 0.5;
      cursor: not-allowed;
      box-shadow: none;
    }

    .danger-button {
      background: rgba(239, 68, 68, 0.18);
      border-color: rgba(239, 68, 68, 0.42);
      color: #fca5a5;
    }

    .danger-button:hover {
      background: rgba(239, 68, 68, 0.28);
      border-color: rgba(248, 113, 113, 0.6);
      color: #fecaca;
    }

    .empty-state {
      padding: 2.5rem;
      border: 1px dashed rgba(148, 163, 184, 0.24);
      border-radius: 12px;
      text-align: center;
      color: var(--text-soft);
      margin-top: 1rem;
    }

    .slot-layout {
      display: grid;
      grid-template-columns: minmax(240px, 280px) 1fr;
      gap: 1.5rem;
    }

    .session-panel {
      background: rgba(15, 15, 25, 0.55);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      max-height: calc(100vh - 200px);
      overflow-y: auto;
    }

    .session-panel h2 {
      margin: 0;
      font-size: 1rem;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--text-soft);
    }

    .session-list {
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
    }

    .session-item {
      border-radius: 10px;
      padding: 0.6rem 0.75rem;
      border: 1px solid transparent;
      background: rgba(148, 163, 184, 0.05);
      text-align: left;
      color: inherit;
      cursor: pointer;
      transition: all 0.18s ease;
    }

    .session-item strong {
      display: block;
      font-size: 0.85rem;
      color: var(--text);
    }

    .session-item span {
      display: block;
      font-size: 0.75rem;
      color: var(--text-soft);
    }

    .session-item:hover {
      border-color: var(--accent);
      background: var(--accent-soft);
    }

    .session-item.active {
      border-color: var(--accent);
      background: rgba(2, 132, 199, 0.28);
      box-shadow: 0 10px 24px rgba(14, 165, 233, 0.22);
    }

    .session-detail {
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .session-summary {
      background: rgba(12, 12, 20, 0.6);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1rem 1.25rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .summary-row {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      align-items: baseline;
      justify-content: space-between;
    }

    .summary-row h2 {
      margin: 0;
      font-size: 1.2rem;
    }

    .prompt-block {
      background: rgba(148, 163, 184, 0.08);
      border-radius: 10px;
      padding: 0.75rem;
      font-size: 0.9rem;
      line-height: 1.5;
      color: var(--text-soft);
      white-space: pre-wrap;
    }

    .warnings {
      border-radius: 12px;
      border: 1px solid var(--warning-soft);
      background: rgba(249, 115, 22, 0.08);
      padding: 0.85rem 1rem;
      color: var(--warning);
    }

    .warnings ul {
      margin: 0.5rem 0 0;
      padding-left: 1.1rem;
      color: var(--text);
    }

    .variant-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 1.25rem;
    }

    .variant-card {
      position: relative;
      border-radius: 14px;
      border: 1px solid var(--border);
      background: rgba(17, 24, 39, 0.55);
      overflow: hidden;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      padding: 0.75rem;
    }

    .variant-header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.5rem;
    }

    .variant-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 0.35rem;
    }

    .variant-session {
      font-size: 0.78rem;
      color: var(--text-soft);
      white-space: nowrap;
    }

    .variant-card.is-selected {
      border-color: var(--accent);
      box-shadow: 0 16px 36px rgba(14, 165, 233, 0.28);
    }

    .variant-thumb {
      position: relative;
      border-radius: 10px;
      overflow: hidden;
      background: rgba(148, 163, 184, 0.08);
      aspect-ratio: 4 / 3;
    }

    .variant-thumb img {
      width: 100%;
      height: 100%;
      object-fit: contain;
      background: #0d1117;
    }

    .badge-selected {
      position: absolute;
      top: 0.75rem;
      left: 0.75rem;
      background: rgba(34, 197, 94, 0.24);
      color: #4ade80;
      padding: 0.25rem 0.6rem;
      border-radius: 999px;
      font-size: 0.7rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-weight: 600;
      backdrop-filter: blur(8px);
    }

    .variant-info {
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
      font-size: 0.78rem;
      color: var(--text-soft);
    }

    .variant-info strong {
      font-size: 0.85rem;
      color: var(--text);
    }

    .variant-stats {
      display: flex;
      flex-wrap: wrap;
      gap: 0.55rem;
      font-size: 0.75rem;
      color: var(--text-soft);
    }

    .variant-actions {
      display: flex;
      flex-wrap: wrap;
      gap: 0.5rem;
    }

    .overlay {
      position: fixed;
      inset: 0;
      background: rgba(8, 8, 12, 0.85);
      backdrop-filter: blur(14px);
      display: flex;
      align-items: center;
      justify-content: center;
      z-index: 50;
    }

    .overlay.hidden { display: none; }

    .overlay-card {
      width: min(90vw, 640px);
      max-height: 80vh;
      overflow-y: auto;
      background: rgba(12, 12, 20, 0.95);
      border: 1px solid var(--border);
      border-radius: 16px;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 1rem;
      box-shadow: 0 24px 64px rgba(2, 132, 199, 0.35);
    }

    .overlay-card h2 {
      margin: 0;
    }

    .overlay-grid {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 0.75rem 1rem;
      font-size: 0.85rem;
    }

    .overlay-grid dt {
      font-weight: 600;
      color: var(--text-soft);
    }

    .overlay-grid dd {
      margin: 0;
      color: var(--text);
      word-break: break-word;
    }

    pre.metadata-json {
      background: rgba(15, 23, 42, 0.7);
      padding: 0.9rem;
      border-radius: 10px;
      overflow-x: auto;
      border: 1px solid rgba(148, 163, 184, 0.16);
      font-size: 0.75rem;
      color: var(--text-soft);
    }

    .toast {
      position: fixed;
      bottom: 1.5rem;
      left: 50%;
      transform: translateX(-50%);
      padding: 0.75rem 1.2rem;
      border-radius: 999px;
      background: rgba(15, 23, 42, 0.82);
      border: 1px solid rgba(56, 189, 248, 0.35);
      color: var(--text);
      font-size: 0.85rem;
      box-shadow: 0 10px 30px rgba(14, 165, 233, 0.25);
      z-index: 60;
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.3s ease;
    }

    .toast.visible { opacity: 1; }

    .hidden { display: none !important; }

    @media (max-width: 720px) {
      .top-bar {
        flex-direction: column;
        align-items: flex-start;
        gap: 0.75rem;
      }
      .top-actions {
        width: 100%;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 0.6rem;
      }
      .project-switcher {
        width: 100%;
        justify-content: space-between;
      }
    }

    @media (max-width: 960px) {
      main { padding: 1rem; }
      .slot-layout {
        grid-template-columns: 1fr;
      }
      .session-panel { max-height: none; }
      .campaign-layout {
        flex-direction: column;
      }
      .campaign-sidebar {
        width: 100%;
      }
    }
  </style>
</head>
<body>
  <div id="app">
    <header class="top-bar">
      <div class="brand-group">
        <div class="brand">ImageMCP Gallery</div>
        <div class="view-tabs">
          <button id="tab-slots" class="ghost-button" type="button" data-active="true">Slots</button>
          <button id="tab-campaigns" class="ghost-button" type="button" data-active="false">Campaigns</button>
        </div>
      </div>
      <div class="top-actions">
        <div class="project-switcher">
          <label for="project-select">Project</label>
          <select id="project-select"></select>
        </div>
        <button id="refresh-slots" class="ghost-button" type="button">Refresh</button>
        <a href="https://github.com/severindeutschmann/ImageMCP" target="_blank" rel="noreferrer" class="ghost-button" style="display:inline-flex;align-items:center;">
          Docs ↗
        </a>
      </div>
    </header>
    <main>
      <section id="slots-view" class="view active">
        <div class="view-header">
          <div>
            <h1>Image Slots</h1>
            <span id="project-label" class="view-subtitle"></span>
          </div>
          <div class="view-actions">
            <button id="filter-warnings" class="ghost-button" data-active="false" type="button">Warnings only</button>
          </div>
        </div>
        <div id="slot-grid" class="slot-grid"></div>
        <div id="slots-empty" class="empty-state hidden">
          No image slots yet. Run <code>imgen gen --slot &lt;name&gt; ...</code> to create the first session.
        </div>
      </section>

      <section id="slot-detail" class="view hidden">
        <div class="view-header">
          <div style="display:flex;gap:0.75rem;align-items:center;">
            <button id="back-to-slots" class="ghost-button" type="button">↩ All slots</button>
            <div>
              <h1 id="slot-title">Slot</h1>
              <span id="slot-subtitle" style="font-size:0.85rem;color:var(--text-soft);"></span>
            </div>
          </div>
          <div class="view-actions">
            <button id="open-selected" class="ghost-button" type="button">Open selected</button>
            <button id="refresh-slot" class="ghost-button" type="button">Refresh</button>
            <button id="delete-slot" class="danger-button" type="button">Delete slot</button>
          </div>
        </div>
        <div class="slot-layout">
          <aside class="session-panel">
            <h2>Sessions</h2>
            <div id="session-list" class="session-list"></div>
            <div id="sessions-empty" class="empty-state hidden">No sessions yet for this slot.</div>
          </aside>
          <section class="session-detail">
            <div id="session-summary" class="session-summary hidden"></div>
            <div id="session-warnings" class="warnings hidden"></div>
            <div id="variant-grid" class="variant-grid"></div>
            <div id="variant-empty" class="empty-state hidden">No variants yet. Generate images to populate this gallery.</div>
          </section>
        </div>
      </section>

      <section id="campaigns-view" class="view hidden">
        <div class="view-header">
          <div>
            <h1>Campaigns</h1>
            <span id="campaigns-subtitle" class="view-subtitle"></span>
          </div>
          <div class="view-actions">
            <input id="campaign-search" type="search" placeholder="Search campaigns" class="input-control" />
            <select id="campaign-status-filter" class="input-control">
              <option value="all">All statuses</option>
              <option value="active">Active</option>
              <option value="draft">Draft</option>
              <option value="on_hold">On hold</option>
              <option value="completed">Completed</option>
            </select>
            <button id="refresh-campaigns" class="ghost-button" type="button">Refresh</button>
          </div>
        </div>
        <div class="campaign-dashboard">
          <div class="campaign-summary-grid" id="campaign-summary-grid"></div>
          <aside class="campaign-dashboard-side">
            <div class="panel">
              <div class="panel-header">
                <h2>Overview</h2>
              </div>
              <div id="campaign-overview-metrics" class="metric-list"></div>
            </div>
            <div class="panel">
              <div class="panel-header">
                <h2>Alerts</h2>
              </div>
              <div id="campaign-alerts" class="alert-list"></div>
            </div>
            <div class="panel">
              <div class="panel-header">
                <h2>Quick Actions</h2>
              </div>
              <div id="campaign-quick-actions" class="action-list"></div>
            </div>
          </aside>
        </div>
        <div id="campaigns-empty" class="empty-state hidden">No campaigns yet. Run <code>imgen campaign init ...</code> to scaffold your first brief.</div>
      </section>

      <section id="campaign-detail" class="view hidden">
        <div class="view-header">
          <div class="view-title-group">
            <button id="back-to-campaigns" class="ghost-button" type="button">↩ Campaigns</button>
            <div>
              <h1 id="campaign-title">Campaign</h1>
              <span id="campaign-subtitle" class="view-subtitle"></span>
            </div>
          </div>
          <div class="view-actions">
            <button id="campaign-copy-status" class="ghost-button" type="button">Copy status JSON</button>
            <button id="refresh-campaign-detail" class="ghost-button" type="button">Refresh</button>
          </div>
        </div>
        <div class="campaign-detail-layout">
          <aside class="campaign-summary-column">
            <div class="panel" id="campaign-summary"></div>
            <div class="panel">
              <div class="filter-group">
                <label>
                  <span>Filter by route</span>
                  <select id="campaign-filter-route"></select>
                </label>
                <label>
                  <span>Filter by placement</span>
                  <select id="campaign-filter-placement"></select>
                </label>
                <label>
                  <span>Review state</span>
                  <select id="campaign-filter-state">
                    <option value="all">All states</option>
                    <option value="approved">Approved</option>
                    <option value="pending">Pending</option>
                    <option value="revise">Revise</option>
                  </select>
                </label>
              </div>
            </div>
            <div class="panel">
              <div class="panel-header"><h2>Placements</h2></div>
              <div id="campaign-progress-list" class="progress-list"></div>
            </div>
            <div class="panel">
              <div class="panel-header"><h2>Routes</h2></div>
              <div id="campaign-route-list" class="campaign-route-list"></div>
            </div>
            <div class="panel">
              <div class="panel-header"><h2>Manifests</h2></div>
              <div id="campaign-manifests" class="manifest-list"></div>
            </div>
            <div class="panel">
              <div class="panel-header"><h2>Exports</h2></div>
              <div id="campaign-exports" class="campaign-export-list"></div>
            </div>
            <div class="panel">
              <div class="panel-header"><h2>Batch Logs</h2></div>
              <div id="campaign-logs" class="campaign-log-list"></div>
            </div>
          </aside>
          <section class="campaign-main-panel">
            <div id="campaign-review-modes" class="review-mode-selection hidden">
              <button class="review-mode-card" type="button" data-mode="focus">
                <h3>Focus Mode</h3>
                <p>Work one placement at a time with a hero view and keyboard approvals.</p>
              </button>
              <button class="review-mode-card" type="button" data-mode="blitz">
                <h3>Blitz Mode</h3>
                <p>Skim every variant quickly, grouped by placement. Click to approve or revise.</p>
              </button>
            </div>
            <div id="campaign-alert-banner" class="alert-banner hidden"></div>
            <div id="campaign-grid" class="campaign-matrix-grid"></div>
            <div id="campaign-empty" class="empty-state hidden">No variants generated yet.</div>
          </section>
        </div>
      </section>
    </main>
  </div>

  <div id="metadata-overlay" class="overlay hidden">
    <div class="overlay-card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;">
        <h2 id="metadata-title">Variant details</h2>
        <button id="metadata-close" class="ghost-button" type="button">Close</button>
      </div>
      <dl id="metadata-grid" class="overlay-grid"></dl>
      <pre id="metadata-json" class="metadata-json"></pre>
    </div>
  </div>

  <div id="campaign-overlay" class="overlay hidden">
    <div class="overlay-card campaign-variant-overlay">
      <header class="overlay-header">
        <div class="overlay-title-group">
          <h2 id="campaign-overlay-title">Variant review</h2>
          <div id="campaign-overlay-subtitle" class="overlay-subtitle"></div>
        </div>
        <button id="campaign-overlay-close" class="ghost-button" type="button">Close</button>
      </header>
      <div class="campaign-overlay-controls">
        <label class="control">
          <span>Variant A</span>
          <select id="campaign-overlay-primary"></select>
        </label>
        <label class="control">
          <span>Variant B</span>
          <select id="campaign-overlay-secondary"></select>
        </label>
      </div>
      <div class="campaign-overlay-body">
        <div class="variant-compare">
          <div class="variant-column">
            <div class="variant-preview">
              <img id="campaign-overlay-image-a" alt="Variant A preview" />
            </div>
            <div id="campaign-overlay-info-a" class="variant-meta"></div>
          </div>
          <div class="variant-column">
            <div class="variant-preview">
              <img id="campaign-overlay-image-b" alt="Variant B preview" />
            </div>
            <div id="campaign-overlay-info-b" class="variant-meta"></div>
          </div>
        </div>
        <div class="campaign-overlay-meta">
          <section>
            <h3>Prompt diff</h3>
            <div id="campaign-overlay-prompt-diff" class="prompt-diff"></div>
          </section>
          <section>
            <h3>Review timeline</h3>
            <div id="campaign-overlay-timeline" class="timeline"></div>
          </section>
          <section>
            <h3>Notes</h3>
            <textarea id="campaign-overlay-notes" placeholder="Add review notes"></textarea>
          </section>
        </div>
      </div>
      <footer class="campaign-overlay-footer">
        <div class="campaign-overlay-actions-left">
          <button id="campaign-overlay-download" class="ghost-button" type="button">Download image</button>
          <button id="campaign-overlay-open" class="ghost-button" type="button">Open file</button>
          <button id="campaign-overlay-copy-json" class="ghost-button" type="button">Copy variant JSON</button>
          <button id="campaign-overlay-copy-command" class="ghost-button" type="button">Copy regenerate command</button>
        </div>
        <div class="campaign-overlay-actions">
          <button id="campaign-overlay-reset" class="ghost-button" type="button">Reset</button>
          <select id="campaign-overlay-state">
            <option value="approved">Approve</option>
            <option value="pending">Pending</option>
            <option value="revise">Request revise</option>
          </select>
          <button id="campaign-overlay-apply" class="primary-button" type="button">Save review</button>
        </div>
      </footer>
      <pre id="campaign-overlay-json" class="metadata-json"></pre>
    </div>
  </div>

  <div id="focus-overlay" class="overlay hidden">
    <div class="overlay-card focus-overlay-card">
      <div class="focus-header">
        <div class="focus-context">
          <h2 id="focus-title">Focus review</h2>
          <div id="focus-subtitle" class="overlay-subtitle"></div>
        </div>
        <button id="focus-close" class="ghost-button" type="button">Close</button>
      </div>
      <div class="focus-hero">
        <img id="focus-hero-image" alt="Selected variant preview" />
        <div id="focus-hero-placeholder" class="focus-hero-placeholder hidden">Use ←/→ to choose a variant</div>
      </div>
      <div class="focus-strip-wrapper">
        <div class="focus-actions-left">←/→ navigate · ↑ approve · ↓ revise</div>
        <div id="focus-strip" class="focus-strip"></div>
      </div>
      <div class="focus-actions">
        <div class="focus-actions-left" id="focus-progress"></div>
        <div class="focus-actions-right" style="display:flex;gap:0.6rem;">
          <button id="focus-approve" class="primary-button" type="button">Approve ▲</button>
          <button id="focus-revise" class="ghost-button" type="button">Revise ▼</button>
        </div>
      </div>
      <div id="focus-notes" class="focus-notes">
        <label for="focus-notes-input" style="font-size:0.8rem;color:var(--text-soft);">Revision notes</label>
        <textarea id="focus-notes-input" placeholder="Tell us what to fix"></textarea>
        <div style="display:flex;justify-content:flex-end;gap:0.5rem;">
          <button id="focus-notes-cancel" class="ghost-button" type="button">Cancel</button>
          <button id="focus-notes-save" class="primary-button" type="button">Save revision</button>
        </div>
      </div>
    </div>
  </div>

  <div id="blitz-overlay" class="overlay hidden">
    <div class="overlay-card blitz-overlay-card">
      <div class="blitz-header">
        <div>
          <h2 id="blitz-title">Variant blitz</h2>
          <div id="blitz-subtitle" class="overlay-subtitle"></div>
        </div>
        <div style="display:flex;gap:0.75rem;align-items:center;">
          <label style="display:flex;flex-direction:column;gap:0.2rem;font-size:0.75rem;color:var(--text-soft);">
            <span>State</span>
            <select id="blitz-filter-state" class="input-control" style="min-width:150px;">
              <option value="all">All</option>
              <option value="approved">Approved</option>
              <option value="pending">Pending</option>
              <option value="revise">Revise</option>
            </select>
          </label>
          <button id="blitz-close" class="ghost-button" type="button">Close</button>
        </div>
      </div>
      <div class="blitz-summary">
        <div>Approved <strong id="blitz-approved-count">0</strong></div>
        <div>Pending <strong id="blitz-pending-count">0</strong></div>
        <div>Revise <strong id="blitz-revise-count">0</strong></div>
      </div>
      <div id="blitz-content" class="blitz-content"></div>
    </div>
  </div>

  <div id="toast" class="toast hidden"></div>

  <script>
    (function() {
      const state = {
        projects: [],
        projectId: null,
        projectName: null,
        slots: [],
        slot: null,
        sessions: [],
        variants: [],
        sessionFilter: null,
        currentSelection: null,
        filterWarnings: false,
        pendingSlot: null,
        viewMode: 'slots',
        campaigns: [],
        campaignStatusFilter: 'all',
        campaignSearch: '',
        campaignFilters: { route: 'all', placement: 'all', state: 'all' },
        selectedCampaignId: null,
        campaignDetail: null,
        pendingCampaign: null,
        activeCampaignVariant: null,
        focusMode: null,
        blitzMode: null,
      };

      const FOCUS_STORAGE_KEY = 'imagemcp:focus-mode';
      const FOCUS_NEXT_SENTINEL = -9999;

      const urlParams = new URLSearchParams(window.location.search);
      const initialProjectParam = urlParams.get('project');
      const initialSlotParam = urlParams.get('slot');
      state.pendingSlot = initialSlotParam;
      const initialCampaignParam = urlParams.get('campaign');
      state.pendingCampaign = initialCampaignParam;
      if (state.pendingCampaign) {
        state.viewMode = 'campaigns';
      }

      const slotGrid = document.getElementById('slot-grid');
      const slotsEmpty = document.getElementById('slots-empty');
      const slotsEmptyDefault = slotsEmpty ? slotsEmpty.innerHTML : '';
      const slotsView = document.getElementById('slots-view');
      const slotDetailView = document.getElementById('slot-detail');
      const slotTitle = document.getElementById('slot-title');
      const slotSubtitle = document.getElementById('slot-subtitle');
      const sessionList = document.getElementById('session-list');
      const sessionsEmpty = document.getElementById('sessions-empty');
      const sessionSummary = document.getElementById('session-summary');
      const sessionWarnings = document.getElementById('session-warnings');
      const variantGrid = document.getElementById('variant-grid');
      const variantEmpty = document.getElementById('variant-empty');
      const toast = document.getElementById('toast');
      const metadataOverlay = document.getElementById('metadata-overlay');
      const metadataGrid = document.getElementById('metadata-grid');
      const metadataJson = document.getElementById('metadata-json');
      const metadataTitle = document.getElementById('metadata-title');

      const tabSlots = document.getElementById('tab-slots');
      const tabCampaigns = document.getElementById('tab-campaigns');
      const campaignsView = document.getElementById('campaigns-view');
      const campaignDetailView = document.getElementById('campaign-detail');
      const campaignsSubtitle = document.getElementById('campaigns-subtitle');
      const campaignSummaryGrid = document.getElementById('campaign-summary-grid');
      const campaignOverviewMetrics = document.getElementById('campaign-overview-metrics');
      const campaignAlertsPanel = document.getElementById('campaign-alerts');
      const campaignQuickActions = document.getElementById('campaign-quick-actions');
      const campaignsEmpty = document.getElementById('campaigns-empty');
      const campaignSearchInput = document.getElementById('campaign-search');
      const campaignStatusFilter = document.getElementById('campaign-status-filter');
      const refreshCampaignsBtn = document.getElementById('refresh-campaigns');

      const campaignTitle = document.getElementById('campaign-title');
      const campaignSubtitle = document.getElementById('campaign-subtitle');
      const campaignSummary = document.getElementById('campaign-summary');
      const campaignProgressList = document.getElementById('campaign-progress-list');
      const campaignRouteList = document.getElementById('campaign-route-list');
      const campaignManifests = document.getElementById('campaign-manifests');
      const campaignExports = document.getElementById('campaign-exports');
      const campaignLogs = document.getElementById('campaign-logs');
      const campaignGrid = document.getElementById('campaign-grid');
      const campaignEmpty = document.getElementById('campaign-empty');
      const campaignAlertBanner = document.getElementById('campaign-alert-banner');
      const campaignFilterRoute = document.getElementById('campaign-filter-route');
      const campaignFilterPlacement = document.getElementById('campaign-filter-placement');
      const campaignFilterState = document.getElementById('campaign-filter-state');
      const backToCampaignsBtn = document.getElementById('back-to-campaigns');
      const refreshCampaignDetailBtn = document.getElementById('refresh-campaign-detail');
      const campaignCopyStatusBtn = document.getElementById('campaign-copy-status');

      const campaignOverlay = document.getElementById('campaign-overlay');
      const campaignOverlayClose = document.getElementById('campaign-overlay-close');
      const campaignOverlayApply = document.getElementById('campaign-overlay-apply');
      const campaignOverlayReset = document.getElementById('campaign-overlay-reset');
      const campaignOverlayState = document.getElementById('campaign-overlay-state');
      const campaignOverlayNotes = document.getElementById('campaign-overlay-notes');
      const campaignOverlayPrimary = document.getElementById('campaign-overlay-primary');
      const campaignOverlaySecondary = document.getElementById('campaign-overlay-secondary');
      const campaignOverlayImageA = document.getElementById('campaign-overlay-image-a');
      const campaignOverlayImageB = document.getElementById('campaign-overlay-image-b');
      const campaignOverlayInfoA = document.getElementById('campaign-overlay-info-a');
      const campaignOverlayInfoB = document.getElementById('campaign-overlay-info-b');
      const campaignOverlayPromptDiff = document.getElementById('campaign-overlay-prompt-diff');
      const campaignOverlayTimeline = document.getElementById('campaign-overlay-timeline');
      const campaignOverlayDownload = document.getElementById('campaign-overlay-download');
      const campaignOverlayOpen = document.getElementById('campaign-overlay-open');
      const campaignOverlayCopyJson = document.getElementById('campaign-overlay-copy-json');
      const campaignOverlayCopyCommand = document.getElementById('campaign-overlay-copy-command');
      const campaignOverlaySubtitle = document.getElementById('campaign-overlay-subtitle');
      const campaignOverlayJson = document.getElementById('campaign-overlay-json');
      const reviewModeSection = document.getElementById('campaign-review-modes');
      const reviewModeCards = reviewModeSection ? Array.from(reviewModeSection.querySelectorAll('.review-mode-card')) : [];
      const focusOverlay = document.getElementById('focus-overlay');
      const focusClose = document.getElementById('focus-close');
      const focusTitle = document.getElementById('focus-title');
      const focusSubtitle = document.getElementById('focus-subtitle');
      const focusHeroImage = document.getElementById('focus-hero-image');
      const focusHeroPlaceholder = document.getElementById('focus-hero-placeholder');
      const focusStrip = document.getElementById('focus-strip');
      const focusApproveBtn = document.getElementById('focus-approve');
      const focusReviseBtn = document.getElementById('focus-revise');
      const focusProgress = document.getElementById('focus-progress');
      const focusNotes = document.getElementById('focus-notes');
      const focusNotesInput = document.getElementById('focus-notes-input');
      const focusNotesCancel = document.getElementById('focus-notes-cancel');
      const focusNotesSave = document.getElementById('focus-notes-save');
      const blitzOverlay = document.getElementById('blitz-overlay');
      const blitzClose = document.getElementById('blitz-close');
      const blitzFilterState = document.getElementById('blitz-filter-state');
      const blitzContent = document.getElementById('blitz-content');
      const blitzApprovedCount = document.getElementById('blitz-approved-count');
      const blitzPendingCount = document.getElementById('blitz-pending-count');
      const blitzReviseCount = document.getElementById('blitz-revise-count');
      const blitzTitle = document.getElementById('blitz-title');
      const blitzSubtitle = document.getElementById('blitz-subtitle');

      let focusKeyHandler = null;
      let blitzKeyHandler = null;

      const projectSelect = document.getElementById('project-select');
      const projectLabel = document.getElementById('project-label');

      if (projectLabel) {
        projectLabel.textContent = 'Loading projects…';
      }

      const refreshSlotsBtn = document.getElementById('refresh-slots');
      const refreshSlotBtn = document.getElementById('refresh-slot');
      const filterWarningsBtn = document.getElementById('filter-warnings');
      const backToSlotsBtn = document.getElementById('back-to-slots');
      const openSelectedBtn = document.getElementById('open-selected');
      const metadataCloseBtn = document.getElementById('metadata-close');
      const deleteSlotBtn = document.getElementById('delete-slot');

      if (deleteSlotBtn) {
        deleteSlotBtn.disabled = true;
      }

      function showToast(message, kind = 'info') {
        toast.textContent = message;
        toast.dataset.kind = kind;
        toast.classList.remove('hidden');
        toast.classList.add('visible');
        clearTimeout(showToast._timer);
        showToast._timer = setTimeout(() => {
          toast.classList.remove('visible');
        }, 2600);
      }

      function escapeHtml(text) {
        if (text === null || text === undefined) return '';
        return String(text)
          .replace(/&/g, '&amp;')
          .replace(/</g, '&lt;')
          .replace(/>/g, '&gt;')
          .replace(/"/g, '&quot;')
          .replace(/'/g, '&#39;');
      }

      function formatTimestamp(ts) {
        if (!ts) return 'n/a';
        try {
          const date = new Date(ts);
          if (Number.isNaN(date.getTime())) return ts;
          return date.toLocaleString();
        } catch (error) {
          return ts;
        }
      }

      function getProjectById(projectId) {
        if (!projectId) return null;
        return state.projects.find((item) => item.projectId === projectId) || null;
      }

      function getProjectName(projectId) {
        const project = getProjectById(projectId);
        if (!project) return null;
        return project.projectName || project.projectId;
      }

      function updateDocumentTitle() {
        if (state.projectName) {
          document.title = `ImageMCP Gallery · ${state.projectName}`;
        } else {
          document.title = 'ImageMCP Gallery';
        }
      }

      function updateProjectSummary() {
        if (!projectLabel) return;
        if (!state.projectId) {
          projectLabel.textContent = 'No project selected';
          return;
        }
        const label = getProjectName(state.projectId) || state.projectId;
        projectLabel.textContent = `Project: ${label}`;
      }

      function renderProjectSelector() {
        if (!projectSelect) return;
        if (!state.projects.length) {
          projectSelect.innerHTML = '<option value="">No projects</option>';
          projectSelect.disabled = true;
          return;
        }
        projectSelect.disabled = false;
        projectSelect.innerHTML = state.projects
          .map((project) => `<option value="${escapeHtml(project.projectId)}">${escapeHtml(project.projectName || project.projectId)}</option>`)
          .join('');
        if (state.projectId) {
          projectSelect.value = state.projectId;
        }
      }

      function updateUrlState() {
        const params = new URLSearchParams();
        if (state.projectId) {
          params.set('project', state.projectId);
        }
        if (state.slot) {
          params.set('slot', state.slot);
        }
        if (state.selectedCampaignId) {
          params.set('campaign', state.selectedCampaignId);
        }
        const next = params.toString();
        const target = next ? `${window.location.pathname}?${next}` : window.location.pathname;
        const current = `${window.location.pathname}${window.location.search}`;
        if (target !== current) {
          window.history.replaceState(null, '', target);
        }
      }

      function updateViewVisibility() {
        if (tabSlots) {
          tabSlots.dataset.active = state.viewMode === 'slots' ? 'true' : 'false';
        }
        if (tabCampaigns) {
          tabCampaigns.dataset.active = state.viewMode === 'campaigns' ? 'true' : 'false';
        }

        if (state.viewMode === 'slots') {
          const showingDetail = Boolean(state.slot);
          if (slotsView) {
            slotsView.classList.toggle('hidden', showingDetail);
            slotsView.classList.toggle('active', !showingDetail);
          }
          if (slotDetailView) {
            slotDetailView.classList.toggle('hidden', !showingDetail);
            slotDetailView.classList.toggle('active', showingDetail);
          }
          if (campaignsView) {
            campaignsView.classList.add('hidden');
            campaignsView.classList.remove('active');
          }
          if (campaignDetailView) {
            campaignDetailView.classList.add('hidden');
            campaignDetailView.classList.remove('active');
          }
        } else {
          const showingCampaignDetail = Boolean(state.selectedCampaignId && state.campaignDetail);
          if (campaignsView) {
            campaignsView.classList.toggle('hidden', showingCampaignDetail);
            campaignsView.classList.toggle('active', !showingCampaignDetail);
          }
          if (campaignDetailView) {
            campaignDetailView.classList.toggle('hidden', !showingCampaignDetail);
            campaignDetailView.classList.toggle('active', showingCampaignDetail);
          }
          if (slotsView) {
            slotsView.classList.add('hidden');
            slotsView.classList.remove('active');
          }
          if (slotDetailView) {
            slotDetailView.classList.add('hidden');
            slotDetailView.classList.remove('active');
          }
        }
      }

      function setViewMode(mode) {
        if (state.viewMode === mode) {
          updateViewVisibility();
          return;
        }
        state.viewMode = mode;
        updateViewVisibility();
        if (mode === 'campaigns' && !state.campaigns.length && state.projectId) {
          loadCampaigns();
        }
        updateUrlState();
      }

      function resetSlotView() {
        state.slot = null;
        state.sessions = [];
        state.variants = [];
        state.sessionFilter = null;
        state.currentSelection = null;
        sessionList.innerHTML = '';
        sessionSummary.classList.add('hidden');
        sessionWarnings.classList.add('hidden');
        sessionWarnings.innerHTML = '';
        variantGrid.innerHTML = '';
        variantEmpty.classList.add('hidden');
        if (openSelectedBtn) {
          openSelectedBtn.dataset.url = '';
        }
        if (deleteSlotBtn) {
          deleteSlotBtn.disabled = true;
        }
        updateViewVisibility();
      }

      function setProject(projectId, { skipReload = false, updateUrl = true, preserveSlot = false } = {}) {
        if (!projectId) {
          return;
        }
        if (state.projectId === projectId) {
          if (!skipReload) {
            loadSlots();
            if (state.viewMode === 'campaigns') {
              loadCampaigns();
            }
          }
          return;
        }
        const project = getProjectById(projectId);
        state.projectId = projectId;
        state.projectName = project ? (project.projectName || project.projectId) : projectId;
        if (projectSelect) {
          projectSelect.value = projectId;
        }
        state.campaigns = [];
        state.campaignDetail = null;
        state.selectedCampaignId = null;
        state.campaignFilters = { route: 'all', placement: 'all', state: 'all' };
        if (campaignSummaryGrid) {
          campaignSummaryGrid.innerHTML = '';
        }
        if (campaignAlertsPanel) {
          campaignAlertsPanel.innerHTML = '';
        }
        if (campaignQuickActions) {
          campaignQuickActions.innerHTML = '';
        }
        if (campaignGrid) {
          campaignGrid.innerHTML = '';
        }
        renderCampaignList();
        updateViewVisibility();
        if (!preserveSlot) {
          resetSlotView();
          state.pendingSlot = null;
          state.slots = [];
          renderSlots();
        }
        updateProjectSummary();
        updateDocumentTitle();
        if (updateUrl) {
          updateUrlState();
        }
        if (!skipReload) {
          loadSlots();
          if (state.viewMode === 'campaigns') {
            loadCampaigns();
          }
        }
      }

      async function loadProjects() {
        try {
          const res = await fetch('/api/projects');
          if (!res.ok) throw new Error('Failed to load projects');
          const data = await res.json();
          state.projects = Array.isArray(data.projects) ? data.projects : [];
          const defaultProjectId = data.defaultProjectId || (state.projects[0] && state.projects[0].projectId) || null;
          renderProjectSelector();
          let desiredProject = initialProjectParam;
          if (!desiredProject || !getProjectById(desiredProject)) {
            desiredProject = state.projectId || defaultProjectId;
          }
          if (desiredProject) {
            const project = getProjectById(desiredProject);
            state.projectId = desiredProject;
            state.projectName = project ? (project.projectName || project.projectId) : desiredProject;
            if (projectSelect) {
              projectSelect.value = desiredProject;
            }
          } else {
            state.projectId = null;
            state.projectName = null;
          }
          updateProjectSummary();
          updateDocumentTitle();
          if (state.projectId) {
            await loadSlots({ initial: true });
            if (state.viewMode === 'campaigns') {
              await loadCampaigns();
            }
          } else {
            renderSlots();
          }
          if ((!initialProjectParam || !getProjectById(initialProjectParam)) && state.projectId) {
            updateUrlState();
          }
          if (projectSelect) {
            projectSelect.disabled = !state.projects.length;
          }
        } catch (error) {
          console.error(error);
          showToast('Unable to load projects', 'error');
        }
      }

      async function loadSlots(options = {}) {
        const { initial = false, forceReload = false } = options;
        if (!state.projectId) {
          state.slots = [];
          renderSlots();
          updateProjectSummary();
          return;
        }
        try {
          const params = new URLSearchParams({ project: state.projectId });
          if (forceReload) {
            params.set('_', Date.now().toString());
          }
          const fetchOptions = forceReload ? { cache: 'no-store' } : {};
          const res = await fetch(`/api/slots?${params.toString()}`, fetchOptions);
          if (!res.ok) throw new Error('Failed to load slots');
          const data = await res.json();
          state.slots = data.slots || [];
          if (data.projectId) {
            state.projectId = data.projectId;
          }
          if (data.projectName) {
            state.projectName = data.projectName;
          } else {
            state.projectName = getProjectName(state.projectId) || state.projectName;
          }
          renderProjectSelector();
          updateProjectSummary();
          updateDocumentTitle();
          renderSlots();
          if (state.slot) {
            const summary = state.slots.find((item) => item.slot === state.slot);
            if (summary && !state.currentSelection && summary.selectedImageUrl) {
              state.currentSelection = { slotImageUrl: summary.selectedImageUrl };
            }
            updateSlotHeader();
          }
          if (initial && state.pendingSlot) {
            const desiredSlot = state.pendingSlot;
            state.pendingSlot = null;
            if (desiredSlot) {
              const summary = state.slots.find((item) => item.slot === desiredSlot);
              if (summary) {
                await selectSlot(desiredSlot);
              }
            }
          }
        } catch (error) {
          console.error(error);
          showToast('Unable to load slots', 'error');
        }
      }

      function renderSlots() {
        const items = state.filterWarnings
          ? state.slots.filter((slot) => slot.warningCount > 0)
          : state.slots;
        filterWarningsBtn.dataset.active = state.filterWarnings ? 'true' : 'false';
        filterWarningsBtn.textContent = state.filterWarnings ? 'Showing warnings only' : 'Warnings only';
        if (!items.length) {
          slotGrid.innerHTML = '';
          if (slotsEmpty) {
            if (!state.projectId) {
              slotsEmpty.textContent = 'Select or initialize a project to view its image slots.';
            } else {
              slotsEmpty.innerHTML = slotsEmptyDefault;
            }
            slotsEmpty.classList.remove('hidden');
          }
          return;
        }
        if (slotsEmpty) {
          slotsEmpty.classList.add('hidden');
          slotsEmpty.innerHTML = slotsEmptyDefault;
        }
        slotGrid.innerHTML = items
          .map((slot) => {
            const warningBadge = slot.warningCount
              ? `<span class="badge badge-warning">⚠ ${slot.warningCount} warning${slot.warningCount === 1 ? '' : 's'}</span>`
              : '';
            const image = slot.selectedImageUrl
              ? `<img src="${slot.selectedImageUrl}" alt="${escapeHtml(slot.slot)} preview">`
              : '<div class="thumb-placeholder">No preview</div>';
            const updated = slot.lastUpdated ? formatTimestamp(slot.lastUpdated) : 'never';
            const active = state.slot && state.slot === slot.slot;
            return `
              <article class="slot-card ${slot.warningCount ? 'has-warning' : ''}" data-slot="${escapeHtml(slot.slot)}" data-active="${active ? 'true' : 'false'}">
                <div class="thumb">${image}</div>
                <div class="slot-meta">
                  <h2>${escapeHtml(slot.slot)}</h2>
                  <span>Sessions: ${slot.sessionCount}</span>
                  <span>Updated: ${escapeHtml(updated)}</span>
                  ${warningBadge}
                </div>
              </article>
            `;
          })
          .join('');
      }

      async function selectSlot(slotId) {
        state.viewMode = 'slots';
        state.slot = slotId;
        updateViewVisibility();
        await loadSlotData(slotId);
      }

      async function loadSlotData(slotId, options = {}) {
        if (!state.projectId) return;
        const { forceReload = false, preserveFilter = false } = options;
        const previousFilter = preserveFilter ? state.sessionFilter : null;
        try {
          const params = new URLSearchParams({ project: state.projectId });
          if (forceReload) {
            params.set('_', Date.now().toString());
          }
          const fetchOptions = forceReload ? { cache: 'no-store' } : {};
          const res = await fetch(`/api/slots/${encodeURIComponent(slotId)}/sessions?${params.toString()}`, fetchOptions);
          if (!res.ok) throw new Error('Failed to load slot data');
          const data = await res.json();
          state.slot = data.slot || slotId;
          if (data.projectId) {
            state.projectId = data.projectId;
          }
          if (data.projectName) {
            state.projectName = data.projectName;
          } else {
            state.projectName = getProjectName(state.projectId) || state.projectName;
          }
          state.sessions = Array.isArray(data.sessions) ? data.sessions : [];
          state.variants = Array.isArray(data.variants) ? data.variants : [];
          if (preserveFilter && previousFilter) {
            const hasFilter = state.sessions.some((session) => session.sessionId === previousFilter);
            state.sessionFilter = hasFilter ? previousFilter : null;
          } else {
            state.sessionFilter = null;
          }
          state.currentSelection = data.currentSelection || null;
          updateProjectSummary();
          updateDocumentTitle();
          updateSlotHeader();
          renderSlots();
          renderSessionList();
          renderSessionSummary();
          renderVariantFeed();
          updateViewVisibility();
          updateUrlState();
        } catch (error) {
          console.error(error);
          showToast('Unable to load slot data', 'error');
        }
      }

      async function requestSlotDeletion(slotId) {
        if (!slotId) return;
        if (deleteSlotBtn) {
          deleteSlotBtn.disabled = true;
        }
        try {
          const params = new URLSearchParams();
          if (state.projectId) {
            params.set('project', state.projectId);
          }
          const query = params.toString();
          const endpoint = `/api/slots/${encodeURIComponent(slotId)}${query ? `?${query}` : ''}`;
          const res = await fetch(endpoint, { method: 'DELETE' });
          if (!res.ok) throw new Error('Failed to delete slot');
          await res.json();
          showToast(`Deleted slot "${slotId}"`);
          resetSlotView();
          state.pendingSlot = null;
          updateUrlState();
          await loadSlots({ forceReload: true });
        } catch (error) {
          console.error(error);
          showToast('Unable to delete slot', 'error');
          if (deleteSlotBtn) {
            deleteSlotBtn.disabled = false;
          }
        }
      }

      function updateSlotHeader() {
        slotTitle.textContent = state.slot || 'Slot';
        if (deleteSlotBtn) {
          deleteSlotBtn.disabled = !state.slot;
        }
        const latestSession = state.sessions.length ? state.sessions[0] : null;
        const subtitleParts = [];
        if (state.projectName || state.projectId) {
          subtitleParts.push(`Project ${state.projectName || state.projectId}`);
        }
        if (latestSession) {
          subtitleParts.push(`Updated ${formatTimestamp(latestSession.completedAt)}`);
        } else {
          subtitleParts.push('No sessions yet');
        }
        slotSubtitle.textContent = subtitleParts.join(' • ');
        const slotUrl = (state.currentSelection && state.currentSelection.slotImageUrl)
          || (state.sessions.length && state.projectId
            ? `/selected?project=${encodeURIComponent(state.projectId)}&slot=${encodeURIComponent(state.slot)}`
            : null);
        openSelectedBtn.dataset.url = slotUrl || '';
        openSelectedBtn.disabled = !slotUrl;
      }

      function renderSessionList() {
        if (!state.sessions.length) {
          sessionList.innerHTML = '';
          sessionsEmpty.classList.remove('hidden');
          return;
        }
        sessionsEmpty.classList.add('hidden');
        const activeSession = state.sessionFilter;
        const latest = state.sessions[0];
        const items = [];
        items.push(`
          <button class="session-item ${activeSession ? '' : 'active'}" data-session="__all__" type="button">
            <strong>All sessions</strong>
            <span>${state.sessions.length} total • Last ${escapeHtml(formatTimestamp(latest.completedAt))}</span>
          </button>
        `);
        state.sessions.forEach((session) => {
          const isActive = activeSession === session.sessionId;
          const warningBadge = session.warnings && session.warnings.length
            ? `<span>⚠ ${session.warnings.length} warning${session.warnings.length === 1 ? '' : 's'}</span>`
            : '';
          items.push(`
            <button class="session-item ${isActive ? 'active' : ''}" data-session="${escapeHtml(session.sessionId)}" type="button">
              <strong>${escapeHtml(formatTimestamp(session.completedAt))}</strong>
              <span>#${session.selectedIndex} • ${session.variantCount} variant${session.variantCount === 1 ? '' : 's'}</span>
              ${warningBadge}
            </button>
          `);
        });
        sessionList.innerHTML = items.join('');
      }

      function renderSessionSummary() {
        if (!state.sessions.length) {
          sessionSummary.classList.add('hidden');
          sessionWarnings.classList.add('hidden');
          sessionSummary.innerHTML = '';
          sessionWarnings.innerHTML = '';
          return;
        }
        const summarySession = state.sessionFilter
          ? state.sessions.find((item) => item.sessionId === state.sessionFilter)
          : state.sessions[0];
        if (!summarySession) {
          sessionSummary.classList.add('hidden');
          sessionWarnings.classList.add('hidden');
          return;
        }
        if (!state.sessionFilter) {
          sessionSummary.innerHTML = `
            <div class="summary-row">
              <div>
                <h2>All Sessions</h2>
                <span>${state.sessions.length} total runs</span>
              </div>
              <div style="font-size:0.82rem;color:var(--text-soft);text-align:right;">
                <div>Latest completed ${escapeHtml(formatTimestamp(summarySession.completedAt))}</div>
                <div>Pick a session to inspect prompts &amp; warnings.</div>
              </div>
            </div>
          `;
          sessionSummary.classList.remove('hidden');
          sessionWarnings.classList.add('hidden');
          sessionWarnings.innerHTML = '';
          return;
        }
        const provider = summarySession.provider || 'provider?';
        const model = summarySession.model || 'model?';
        const size = summarySession.size || 'size?';
        const prompt = summarySession.prompt || 'No prompt recorded';
        const requestText = summarySession.requestText || '—';
        sessionSummary.innerHTML = `
          <div class="summary-row">
            <div>
              <h2>Session ${escapeHtml(summarySession.sessionId)}</h2>
              <span>Completed ${escapeHtml(formatTimestamp(summarySession.completedAt))}</span>
            </div>
            <div style="font-size:0.82rem;color:var(--text-soft);text-align:right;">
              <div>${escapeHtml(provider)} • ${escapeHtml(model)}</div>
              <div>${escapeHtml(size)}</div>
            </div>
          </div>
          <div style="font-size:0.85rem;color:var(--text-soft);">Request: ${escapeHtml(requestText)}</div>
          <div class="prompt-block">${escapeHtml(prompt)}</div>
          <div style="font-size:0.75rem;color:var(--text-soft);">Created ${escapeHtml(formatTimestamp(summarySession.createdAt))}</div>
        `;
        sessionSummary.classList.remove('hidden');
        if (summarySession.warnings && summarySession.warnings.length) {
          sessionWarnings.innerHTML = `
            <strong>Warnings</strong>
            <ul>${summarySession.warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join('')}</ul>
          `;
          sessionWarnings.classList.remove('hidden');
        } else {
          sessionWarnings.classList.add('hidden');
          sessionWarnings.innerHTML = '';
        }
      }

      function renderVariantFeed() {
        let variants = state.variants;
        if (state.sessionFilter) {
          variants = variants.filter((variant) => variant.sessionId === state.sessionFilter);
        }
        if (!variants.length) {
          variantGrid.innerHTML = '';
          variantEmpty.classList.remove('hidden');
          return;
        }
        variantEmpty.classList.add('hidden');
        variantGrid.innerHTML = variants
          .map((variant) => {
            const cropPercent = typeof variant.cropFraction === 'number'
              ? `${(variant.cropFraction * 100).toFixed(1)}%`
              : '0%';
            const originalLabel = variant.original && variant.original.width
              ? `Original ${variant.original.width}×${variant.original.height}`
              : 'Original n/a';
            const badges = [];
            if (variant.isSlotSelected) {
              badges.push('<span class="badge badge-info">Current slot</span>');
            }
            if (!variant.isSlotSelected && variant.isSessionSelected) {
              badges.push('<span class="badge badge-info">Session pick</span>');
            }
            if (variant.sessionWarnings && variant.sessionWarnings.length) {
              badges.push(`<span class="badge badge-warning">⚠ ${variant.sessionWarnings.length}</span>`);
            }
            const providerLine = [
              variant.sessionProvider || 'provider?',
              variant.sessionModel || 'model?',
              variant.sessionSize || 'size?',
            ].filter(Boolean).join(' • ');
            return `
              <article class="variant-card ${variant.isSlotSelected ? 'is-selected' : ''}" data-session="${escapeHtml(variant.sessionId)}" data-index="${variant.variantIndex}">
                <div class="variant-header">
                  <div class="variant-badges">${badges.join('')}</div>
                  <span class="variant-session">${escapeHtml(formatTimestamp(variant.sessionCompletedAt))}</span>
                </div>
                <div class="variant-thumb">
                  ${variant.isSlotSelected ? '<span class="badge-selected">Slot</span>' : ''}
                  <img src="${variant.processed.url}" alt="Variant ${variant.variantIndex}">
                </div>
                <div class="variant-info">
                  <strong>Session ${escapeHtml(variant.sessionId)} · #${variant.variantIndex}</strong>
                  <div>${escapeHtml(providerLine)}</div>
                  <div class="variant-stats">
                    <span>${variant.processed.width}×${variant.processed.height}</span>
                    <span>${escapeHtml(originalLabel)}</span>
                    <span>Crop ${cropPercent}</span>
                  </div>
                </div>
                <div class="variant-actions">
                  ${variant.raw ? `<button class="ghost-button" data-action="open-raw" data-session="${escapeHtml(variant.sessionId)}" data-index="${variant.variantIndex}" type="button">View raw</button>` : ''}
                  <button class="ghost-button" data-action="metadata" data-session="${escapeHtml(variant.sessionId)}" data-index="${variant.variantIndex}" type="button">Metadata</button>
                  <button class="primary-button" data-action="promote" data-session="${escapeHtml(variant.sessionId)}" data-index="${variant.variantIndex}" type="button" ${variant.isSlotSelected ? 'disabled' : ''}>Use this variant</button>
                </div>
              </article>
            `;
          })
          .join('');
      }

      function getVariant(sessionId, index) {
        return state.variants.find(
          (variant) => variant.sessionId === sessionId && variant.variantIndex === Number(index),
        );
      }

      function openMetadata(sessionId, index) {
        const variant = getVariant(sessionId, index);
        if (!variant) return;
        metadataTitle.textContent = `Variant #${variant.variantIndex} · Session ${variant.sessionId}`;
        const rows = [
          ['Slot', variant.slot],
          ['Session completed', formatTimestamp(variant.sessionCompletedAt)],
          ['Variant index', variant.variantIndex],
          ['Processed file', variant.processed.filename],
          ['Processed size', `${variant.processed.width}×${variant.processed.height}`],
          ['Media type', variant.processed.mediaType],
          ['Raw file', variant.raw ? variant.raw.filename : '—'],
          ['Crop fraction', typeof variant.cropFraction === 'number' ? variant.cropFraction.toFixed(3) : '—'],
          ['Original size', variant.original && variant.original.width ? `${variant.original.width}×${variant.original.height}` : '—'],
          ['Provider', variant.sessionProvider || '—'],
          ['Model', variant.sessionModel || '—'],
          ['Requested size', variant.sessionSize || '—'],
          ['Prompt', variant.sessionPrompt || '—'],
          ['Request text', variant.sessionRequest || '—'],
          ['SHA-256', variant.sha256],
        ];
        metadataGrid.innerHTML = rows
          .map(([label, value]) => `<dt>${escapeHtml(label)}</dt><dd>${escapeHtml(value || '—')}</dd>`)
          .join('');
        metadataJson.textContent = JSON.stringify(variant, null, 2);
        metadataOverlay.classList.remove('hidden');
      }

      function closeMetadata() {
        metadataOverlay.classList.add('hidden');
      }

      async function promoteVariant(sessionId, index) {
        const variant = getVariant(sessionId, index);
        if (!variant) return;
        try {
          const body = new URLSearchParams({
            slot: variant.slot,
            session: variant.sessionId,
            index: String(variant.variantIndex),
          });
          if (state.projectId) {
            body.set('project', state.projectId);
          }
          const res = await fetch('/api/select', {
            method: 'POST',
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
            body,
          });
          if (!res.ok) throw new Error('Promote failed');
          showToast(`Promoted session ${variant.sessionId} #${variant.variantIndex}`);
          await loadSlotData(variant.slot, { forceReload: true, preserveFilter: true });
          await loadSlots({ forceReload: true });
        } catch (error) {
          console.error(error);
          showToast('Unable to promote variant', 'error');
        }
      }

      function getFilteredCampaignSummaries() {
        const needle = state.campaignSearch.trim().toLowerCase();
        return state.campaigns.filter((campaign) => {
          if (state.campaignStatusFilter !== 'all' && campaign.status !== state.campaignStatusFilter) {
            return false;
          }
          if (!needle) return true;
          const haystack = [
            campaign.name,
            campaign.campaignId,
            Array.isArray(campaign.tags) ? campaign.tags.join(' ') : '',
          ].join(' ').toLowerCase();
      return haystack.includes(needle);
    });
  }

  function summarizeCampaignProgress(campaign) {
    const progress = campaign.progress || {};
    const expected = progress.expectedVariants ?? campaign.expectedVariants ?? campaign.variants ?? 0;
    const generated = progress.generatedVariants ?? campaign.generatedVariants ?? campaign.variants ?? 0;
    const pending = progress.pendingVariants ?? campaign.pending ?? 0;
    const percent = progress.progressPercent ?? (expected ? (generated / expected) * 100 : 0);
    return {
      expected,
      generated,
      pending,
      percent: Math.max(0, Math.min(100, percent || 0)),
    };
  }

  function renderCampaignCard(campaign, isActive) {
    const progress = summarizeCampaignProgress(campaign);
    const name = campaign.name || campaign.campaignId;
    const updated = campaign.updatedAt ? formatTimestamp(campaign.updatedAt) : '—';
    const tags = Array.isArray(campaign.tags) && campaign.tags.length
      ? `<div class="campaign-card-meta">${campaign.tags.map((tag) => `<span class="campaign-chip">${escapeHtml(tag)}</span>`).join('')}</div>`
      : '';
    const status = (campaign.status || '').toUpperCase();
    const alerts = Array.isArray(campaign.alerts) ? campaign.alerts.length : 0;
    const alertBadge = alerts
      ? `<span class="alert-pill" title="${alerts} alert${alerts === 1 ? '' : 's'}">⚠ ${alerts}</span>`
      : '';
    const resume = campaign.resume;
    const resumeLabel = resume
      ? `Resume ${escapeHtml(resume.placementId)} · ${escapeHtml(resume.variantLabel)}`
      : '';
    const approved = campaign.approved ?? 0;
    const cardActions = [
      `<button class="ghost-button" type="button" data-action="open" data-campaign="${escapeHtml(campaign.campaignId)}">Open detail</button>`,
      `<button class="ghost-button" type="button" data-action="status" data-campaign="${escapeHtml(campaign.campaignId)}">Status JSON</button>`
    ];
    if (resume) {
      cardActions.unshift(`<button class="primary-button" type="button" data-action="resume" data-campaign="${escapeHtml(campaign.campaignId)}">Resume ${escapeHtml(resume.variantLabel)}</button>`);
    }
    return `
      <article class="campaign-card" data-campaign="${escapeHtml(campaign.campaignId)}" data-active="${isActive ? 'true' : 'false'}">
        <div class="campaign-card-header">
          <div>
            <h2 class="campaign-card-title">${escapeHtml(name)}</h2>
            <div class="campaign-card-meta">
              <span>${escapeHtml(status)}</span>
              <span>${escapeHtml(updated)}</span>
              ${alertBadge}
            </div>
            ${tags}
          </div>
        </div>
        <div>
          <div class="campaign-progress-bar"><span style="width:${progress.percent.toFixed(1)}%;"></span></div>
          <div class="campaign-card-stats">
            <span>${progress.generated}/${progress.expected} generated</span>
            <span>${approved} approved</span>
            <span>${progress.pending} pending</span>
          </div>
          ${resume ? `<div class="campaign-card-meta">${resumeLabel}</div>` : ''}
        </div>
        <div class="campaign-card-actions">
          ${cardActions.join('')}
        </div>
      </article>
    `;
  }

  function aggregateCampaignAlerts(campaigns) {
    const alerts = [];
    campaigns.forEach((campaign) => {
      (campaign.alerts || []).forEach((alert) => {
        alerts.push({ ...alert, campaignId: campaign.campaignId, name: campaign.name || campaign.campaignId });
      });
    });
    return alerts;
  }

  function renderAlertItem(alert) {
    let description = '';
    if (alert.type === 'pendingVariants') {
      description = `${escapeHtml(alert.name)} • ${escapeHtml(alert.placementId)} has ${alert.count} pending variant${alert.count === 1 ? '' : 's'}`;
    } else if (alert.type === 'missingManifest') {
      description = `${escapeHtml(alert.name)} • Missing manifest at ${escapeHtml(alert.manifestPath || '')}`;
    } else if (alert.type === 'awaitingGeneration') {
      description = `${escapeHtml(alert.name)} • ${escapeHtml(alert.placementId)} not generated (${alert.expectedVariants} expected)`;
    } else if (alert.type === 'orphanFile') {
      description = `${escapeHtml(alert.name)} • Orphan file ${escapeHtml(alert.path || '')}`;
    } else {
      description = `${escapeHtml(alert.name)} • ${escapeHtml(alert.type || 'Alert')}`;
    }
    return `<div class="alert-item" data-campaign="${escapeHtml(alert.campaignId)}">${description}</div>`;
  }

  function buildQuickActions(campaigns) {
    const actions = [];
    const resumeCandidate = campaigns.find((item) => item.resume);
    if (resumeCandidate && resumeCandidate.resume) {
      actions.push({
        label: `Resume ${resumeCandidate.name || resumeCandidate.campaignId}`,
        campaignId: resumeCandidate.campaignId,
        action: 'resume',
      });
    }
    if (campaigns.length) {
      const primary = campaigns[0];
      actions.push({ label: `Open ${primary.name || primary.campaignId}`, campaignId: primary.campaignId, action: 'open' });
      actions.push({ label: `Status JSON (${primary.name || primary.campaignId})`, campaignId: primary.campaignId, action: 'status' });
    }
    return actions;
  }

  function renderCampaignList() {
    const items = getFilteredCampaignSummaries();
    const total = state.campaigns.length;
    const selectedId = state.selectedCampaignId;

    if (campaignSummaryGrid) {
      campaignSummaryGrid.innerHTML = items
        .map((campaign) => renderCampaignCard(campaign, selectedId === campaign.campaignId))
        .join('');
    }

    if (campaignsEmpty) {
      campaignsEmpty.classList.toggle('hidden', Boolean(items.length));
    }

    if (campaignsSubtitle) {
      if (!state.projectId) {
        campaignsSubtitle.textContent = 'Select a project to view campaign workspaces.';
      } else {
        const projectName = getProjectName(state.projectId) || state.projectId;
        campaignsSubtitle.textContent = `${projectName} • ${items.length}/${total} campaigns`;
      }
    }

    if (campaignOverviewMetrics) {
      const aggregates = items.reduce((acc, campaign) => {
        const progress = summarizeCampaignProgress(campaign);
        acc.expected += progress.expected;
        acc.generated += progress.generated;
        acc.pending += progress.pending;
        acc.approved += campaign.approved ?? 0;
        return acc;
      }, { expected: 0, generated: 0, pending: 0, approved: 0 });
      campaignOverviewMetrics.innerHTML = `
        <div class="metric-item"><span>Total campaigns</span><strong>${total}</strong></div>
        <div class="metric-item"><span>Generated variants</span><strong>${aggregates.generated}/${aggregates.expected}</strong></div>
        <div class="metric-item"><span>Approved variants</span><strong>${aggregates.approved}</strong></div>
        <div class="metric-item"><span>Pending review</span><strong>${aggregates.pending}</strong></div>
      `;
    }

    if (campaignAlertsPanel) {
      const alerts = aggregateCampaignAlerts(items);
      campaignAlertsPanel.innerHTML = alerts.length
        ? alerts.slice(0, 6).map(renderAlertItem).join('')
        : '<div class="empty-note">All clear for now.</div>';
    }

    if (campaignQuickActions) {
      const actions = buildQuickActions(items);
      campaignQuickActions.innerHTML = actions.length
        ? actions.map((action) => `<button class="ghost-button" type="button" data-action="${action.action}" data-campaign="${escapeHtml(action.campaignId)}">${escapeHtml(action.label)}</button>`).join('')
        : '<div class="empty-note">No quick actions available.</div>';
    }
  }

      function showCampaignList() {
        state.selectedCampaignId = null;
        state.campaignDetail = null;
        state.campaignFilters = { route: 'all', placement: 'all', state: 'all' };
        updateViewVisibility();
        renderCampaignList();
        updateUrlState();
      }

      async function loadCampaigns(options = {}) {
        if (!state.projectId) {
          state.campaigns = [];
          renderCampaignList();
          return;
        }
        const { forceReload = false } = options;
        try {
          const params = new URLSearchParams({ project: state.projectId });
          if (forceReload) {
            params.set('_', Date.now().toString());
          }
          const fetchOptions = forceReload ? { cache: 'no-store' } : {};
          const res = await fetch(`/api/campaigns?${params.toString()}`, fetchOptions);
          if (!res.ok) throw new Error('Failed to load campaigns');
          const data = await res.json();
          state.campaigns = Array.isArray(data.campaigns) ? data.campaigns : [];
          renderCampaignList();
          updateViewVisibility();
          if (state.viewMode === 'campaigns' && state.selectedCampaignId) {
            const exists = state.campaigns.some((item) => item.campaignId === state.selectedCampaignId);
            if (!exists) {
              showCampaignList();
            }
          }
          if (state.pendingCampaign) {
            const pendingId = state.pendingCampaign;
            state.pendingCampaign = null;
            const found = state.campaigns.some((item) => item.campaignId === pendingId);
            if (found) {
              setViewMode('campaigns');
              selectCampaign(pendingId);
            }
          }
          if (forceReload && state.selectedCampaignId) {
            await loadCampaignDetail(state.selectedCampaignId, { forceReload: true });
          }
        } catch (error) {
          console.error(error);
          showToast('Unable to load campaigns', 'error');
        }
      }

      function populateCampaignFilters(detail) {
        if (!detail) return;
        if (campaignFilterRoute) {
          const options = ['<option value="all">All routes</option>']
            .concat((detail.routes || []).map((route) => {
              const active = state.campaignFilters.route === route.routeId;
              return `<option value="${escapeHtml(route.routeId)}" ${active ? 'selected' : ''}>${escapeHtml(route.name || route.routeId)}</option>`;
            }));
          campaignFilterRoute.innerHTML = options.join('');
          if (state.campaignFilters.route && state.campaignFilters.route !== 'all') {
            campaignFilterRoute.value = state.campaignFilters.route;
          }
        }
        if (campaignFilterPlacement) {
          const options = ['<option value="all">All placements</option>']
            .concat((detail.placements || []).map((placement) => {
              const active = state.campaignFilters.placement === placement.placementId;
              return `<option value="${escapeHtml(placement.placementId)}" ${active ? 'selected' : ''}>${escapeHtml(placement.placementId)}</option>`;
            }));
          campaignFilterPlacement.innerHTML = options.join('');
          if (state.campaignFilters.placement && state.campaignFilters.placement !== 'all') {
            campaignFilterPlacement.value = state.campaignFilters.placement;
          }
        }
        if (campaignFilterState) {
          campaignFilterState.value = state.campaignFilters.state;
        }
      }

      function getCampaignMeta(detail) {
        const placementsMeta = new Map();
        (detail.placements || []).forEach((placement) => {
          placementsMeta.set(placement.placementId, placement);
        });
        const routesMeta = new Map();
        (detail.routes || []).forEach((route) => {
          routesMeta.set(route.routeId, route);
        });
        return { placementsMeta, routesMeta };
      }

      function getFilteredCampaignMatrix(detail) {
        if (!detail) return [];
        const { placementsMeta, routesMeta } = getCampaignMeta(detail);
      const placementFilter = state.campaignFilters.placement;
      const routeFilter = state.campaignFilters.route;
      const stateFilter = state.campaignFilters.state;
      const grouped = new Map();
      (detail.matrix || []).forEach((cell) => {
        if (routeFilter !== 'all' && cell.routeId !== routeFilter) return;
        if (placementFilter !== 'all' && cell.placementId !== placementFilter) return;
        const variants = (cell.variants || []).filter((variant) => {
          if (stateFilter === 'all') return true;
          return variant.reviewState === stateFilter;
        });
        const pendingLabels = cell.pendingVariantLabels || [];
        const hasPendingVariant = pendingLabels.length > 0 || (cell.variants || []).some((variant) => variant.reviewState === 'pending');
        const hasApprovedVariant = (cell.variants || []).some((variant) => variant.reviewState === 'approved');
        const hasReviseVariant = (cell.variants || []).some((variant) => variant.reviewState === 'revise');
        const expectedCount = cell.expectedVariants ?? (cell.variants ? cell.variants.length : 0);

        const includeByState = (
          stateFilter === 'all'
          || (stateFilter === 'pending' && hasPendingVariant)
          || (stateFilter === 'approved' && hasApprovedVariant)
          || (stateFilter === 'revise' && hasReviseVariant)
        );

        if (!includeByState) return;
        if (!variants.length && pendingLabels.length === 0 && expectedCount === 0 && stateFilter !== 'all') {
          return;
        }
        const placementId = cell.placementId;
        if (!grouped.has(placementId)) {
          grouped.set(placementId, {
            placement: placementsMeta.get(placementId) || { placementId },
            routes: [],
          });
        }
        const routeMeta = routesMeta.get(cell.routeId) || { routeId: cell.routeId, name: cell.routeId, summary: cell.routeSummary };
        grouped.get(placementId).routes.push({
          routeId: cell.routeId,
          route: routeMeta,
          variants,
          expectedVariants: cell.expectedVariants ?? variants.length,
          generatedVariants: cell.generatedVariants ?? variants.length,
          pendingVariantLabels: pendingLabels,
          pendingVariantIndices: cell.pendingVariantIndices || [],
          extraVariantLabels: cell.extraVariantLabels || [],
          manifestMissing: cell.manifestMissing || [],
          nextVariantIndex: cell.nextVariantIndex,
        });
      });
      return Array.from(grouped.entries())
        .sort((a, b) => a[0].localeCompare(b[0]))
        .map(([placementId, value]) => ({
          placementId,
          placement: value.placement,
          routes: value.routes.sort((a, b) => {
            const nameA = (a.route && a.route.name) || a.routeId;
            const nameB = (b.route && b.route.name) || b.routeId;
            return nameA.localeCompare(nameB);
          }),
        }));
      }

      function renderCampaignDetail() {
        if (!campaignDetailView) return;
        const detail = state.campaignDetail;
        if (!detail || !state.selectedCampaignId) {
          campaignDetailView.classList.add('hidden');
          campaignDetailView.classList.remove('active');
          return;
        }
        renderCampaignList();

        if (reviewModeSection) {
          const hasVariants = (detail.matrix || []).some((cell) => (cell.variants || []).length);
          reviewModeSection.classList.toggle('hidden', !hasVariants);
        }

        if (state.focusMode && state.focusMode.active) {
          refreshFocusQueue();
          renderFocusMode();
        }
        if (state.blitzMode && state.blitzMode.active) {
          renderBlitzMode();
        }

        const campaign = detail.campaign || {};
        const summary = state.campaigns.find((item) => item.campaignId === campaign.campaignId);
        if (summary && detail.stats) {
          summary.updatedAt = campaign.updatedAt || summary.updatedAt;
          summary.approved = detail.stats.approved ?? summary.approved;
          summary.pending = detail.stats.pending ?? summary.pending;
          summary.revise = detail.stats.revise ?? summary.revise;
          summary.variants = detail.stats.total ?? summary.variants;
        }

        campaignTitle.textContent = campaign.name || campaign.campaignId;
        const status = (campaign.status || '').toUpperCase();
        const tagLine = Array.isArray(campaign.tags) && campaign.tags.length
          ? campaign.tags.map((tag) => `<span class="campaign-chip">${escapeHtml(tag)}</span>`).join(' ')
          : '';
        campaignSubtitle.innerHTML = `${escapeHtml(status)} ${tagLine}`;

        const progress = detail.progress || summarizeCampaignProgress({ progress: detail.progress, variants: detail.stats?.total });
        const brief = campaign.brief || {};
        const objective = brief.objective ? escapeHtml(brief.objective) : '—';

        if (campaignSummary) {
          campaignSummary.innerHTML = `
            <div class="metric-list">
              <div class="metric-item"><span>Generated</span><strong>${progress.generatedVariants ?? progress.generated}/${progress.expectedVariants ?? progress.expected}</strong></div>
              <div class="metric-item"><span>Pending</span><strong>${progress.pendingVariants ?? progress.pending}</strong></div>
              <div class="metric-item"><span>Extra variants</span><strong>${progress.extraVariants ?? 0}</strong></div>
            </div>
            <div class="campaign-card-meta"><span>Provider</span><strong>${escapeHtml(campaign.defaultProvider || '—')}</strong></div>
            <div class="campaign-card-meta"><span>Objective</span><strong>${objective}</strong></div>
            <div class="campaign-card-meta"><span>Updated</span><strong>${escapeHtml(formatTimestamp(campaign.updatedAt))}</strong></div>
            ${detail.resume ? `<div class="alert-pill">Resume ${escapeHtml(detail.resume.placementId)} • ${escapeHtml(detail.resume.variantLabel)}</div>` : ''}
          `;
        }

        if (campaignProgressList) {
          const placements = detail.placements || [];
          campaignProgressList.innerHTML = placements.length
            ? placements.map((placement) => {
                const expected = placement.expectedVariants ?? placement.variants ?? 0;
                const generated = placement.generatedVariants ?? placement.variants ?? 0;
                const pending = placement.pendingVariants ?? 0;
                const percent = expected ? Math.min(100, Math.max(0, (generated / expected) * 100)) : 0;
                const manifestLabel = placement.manifestPresent ? 'Manifest synced' : 'Manifest missing';
                return `
                  <div class="progress-item" data-placement="${escapeHtml(placement.placementId)}">
                    <div class="progress-item-header">
                      <strong>${escapeHtml(placement.placementId)}</strong>
                      <span>${generated}/${expected} • Pending ${pending}</span>
                    </div>
                    <div class="campaign-progress-bar"><span style="width:${percent.toFixed(1)}%;"></span></div>
                    <div class="campaign-card-meta">${escapeHtml(manifestLabel)}</div>
                  </div>
                `;
              }).join('')
            : '<div class="empty-note">No placements defined.</div>';
        }

        if (campaignManifests) {
          const placements = detail.placements || [];
          campaignManifests.innerHTML = placements.length
            ? placements.map((placement) => {
                const statusLabel = placement.manifestPresent ? '✅ Present' : '⚠ Missing';
                const pathLabel = placement.manifestPath ? escapeHtml(placement.manifestPath) : 'Not saved';
                return `<div>${escapeHtml(placement.placementId)} · ${statusLabel} · ${pathLabel}</div>`;
              }).join('')
            : '<div class="empty-note">No manifests yet.</div>';
        }

        if (campaignExports) {
          const exports = detail.exports || [];
          campaignExports.innerHTML = exports.length
            ? exports.map((entry) => {
                const includeStates = entry.includeStates || [];
                return `
                  <div class="campaign-export-item">
                    <div style="font-weight:600;">${escapeHtml(entry.platform)} · ${escapeHtml(entry.exportId)}</div>
                    <div>${escapeHtml(formatTimestamp(entry.generatedAt))}</div>
                    <div>${includeStates.join(', ') || 'approved'} • ${entry.fileCount ?? 0} files</div>
                    <div>${escapeHtml(entry.manifestPath || '')}</div>
                  </div>
                `;
              }).join('')
            : '<div class="empty-note">No exports yet.</div>';
        }

        if (campaignLogs) {
          const logs = detail.logs || [];
          campaignLogs.innerHTML = logs.length
            ? logs.map((entry) => `
              <div class="campaign-log-item">
                <div style="font-weight:600;">${escapeHtml(entry.filename)}</div>
                <div>${escapeHtml(formatTimestamp(entry.updatedAt))} · ${entry.sizeBytes ?? 0} bytes</div>
                <div>${escapeHtml(entry.relativePath || '')}</div>
              </div>
            `).join('')
            : '<div class="empty-note">No batch runs yet.</div>';
        }

        if (campaignRouteList) {
          const routes = detail.routes || [];
          const routeStats = new Map();
          (detail.matrix || []).forEach((cell) => {
            const stats = routeStats.get(cell.routeId) || { generated: 0, expected: 0, pending: 0 };
            const generated = cell.generatedVariants ?? (cell.variants ? cell.variants.length : 0);
            const expected = cell.expectedVariants ?? generated;
            const pending = (cell.pendingVariantLabels || []).length;
            stats.generated += generated;
            stats.expected += expected;
            stats.pending += pending;
            routeStats.set(cell.routeId, stats);
          });
          campaignRouteList.innerHTML = routes.length
            ? routes.map((route) => {
                const stats = routeStats.get(route.routeId) || { generated: 0, expected: 0, pending: 0 };
                const active = state.campaignFilters.route === route.routeId;
                return `
                  <div class="campaign-route-card" data-route="${escapeHtml(route.routeId)}" data-active="${active ? 'true' : 'false'}">
                    <div style="font-weight:600;">${escapeHtml(route.name || route.routeId)}</div>
                    <div style="font-size:0.78rem;color:var(--text-soft);">${escapeHtml(route.summary || '')}</div>
                    <div class="campaign-card-meta">${stats.generated}/${stats.expected} generated • ${stats.pending} pending</div>
                  </div>
                `;
              }).join('')
            : '<div class="empty-note">No routes yet.</div>';
        }

        populateCampaignFilters(detail);

        if (campaignAlertBanner) {
          const alerts = detail.alerts || [];
          if (alerts.length) {
            campaignAlertBanner.classList.remove('hidden');
            const alertHtml = alerts.map((alert) => renderAlertItem({ ...alert, campaignId: detail.campaign.campaignId, name: detail.campaign.name || detail.campaign.campaignId })).join('');
            campaignAlertBanner.innerHTML = `${alertHtml}<div class="campaign-card-meta">Run <code>imgen campaign status ${escapeHtml(detail.campaign.campaignId)} --json</code> for a full report.</div>`;
          } else {
            campaignAlertBanner.classList.add('hidden');
            campaignAlertBanner.innerHTML = '';
          }
        }

        const grouped = getFilteredCampaignMatrix(detail);
        if (!grouped.length) {
          campaignGrid.innerHTML = '';
          campaignEmpty.classList.remove('hidden');
        } else {
          campaignEmpty.classList.add('hidden');
          campaignGrid.innerHTML = grouped.map((group) => {
            const placement = group.placement || {};
            const expected = placement.expectedVariants ?? placement.variants ?? 0;
            const generated = placement.generatedVariants ?? placement.variants ?? 0;
            const pending = placement.pendingVariants ?? 0;
            const headerMeta = `${generated}/${expected} generated • ${pending} pending`;
            const routeBlocks = group.routes.map((entry) => {
              const variants = entry.variants || [];
              const pendingText = entry.pendingVariantLabels && entry.pendingVariantLabels.length
                ? `<div class="campaign-card-meta">Pending ${entry.pendingVariantLabels.map(escapeHtml).join(', ')}</div>`
                : '';
              const variantStrip = variants.length
                ? variants.map((variant) => {
                    const thumb = variant.thumbnailUrl
                      ? `<img src="${variant.thumbnailUrl}" alt="Variant ${variant.index}">`
                      : '<div class="thumb-placeholder">No thumb</div>';
                    return `
                      <button type="button" class="campaign-variant-thumb" data-route="${escapeHtml(entry.routeId)}" data-placement="${escapeHtml(group.placementId)}" data-index="${variant.index}" data-state="${escapeHtml(variant.reviewState)}">
                        ${thumb}
                      </button>
                    `;
                  }).join('')
                : '<div class="empty-note">No variants yet.</div>';
              return `
                <article class="campaign-route-section">
                  <div class="campaign-route-header">
                    <div>
                      <div class="campaign-route-name">${escapeHtml(entry.route.name || entry.routeId)}</div>
                      <div class="campaign-card-meta">${entry.generatedVariants}/${entry.expectedVariants} generated</div>
                    </div>
                  </div>
                  ${pendingText}
                  <div class="campaign-variant-strip">${variantStrip}</div>
                </article>
              `;
            }).join('');
            return `
              <section class="campaign-matrix-card" data-placement="${escapeHtml(group.placementId)}">
                <header>
                  <div>
                    <h2>${escapeHtml(group.placementId)}</h2>
                    <div class="campaign-card-meta">${escapeHtml(placement.templateId || '')}</div>
                  </div>
                  <div class="campaign-card-meta">${headerMeta}</div>
                </header>
                ${routeBlocks}
              </section>
            `;
          }).join('');
        }

        updateViewVisibility();
        updateUrlState();
      }

      async function selectCampaign(campaignId) {
        if (!campaignId) return;
        state.viewMode = 'campaigns';
        state.selectedCampaignId = campaignId;
        state.campaignFilters = { route: 'all', placement: 'all', state: 'all' };
        renderCampaignList();
        updateViewVisibility();
        await loadCampaignDetail(campaignId);
      }

      async function loadCampaignDetail(campaignId, { forceReload = false } = {}) {
        if (!state.projectId || !campaignId) return;
        try {
          const params = new URLSearchParams({ project: state.projectId });
          if (forceReload) params.set('_', Date.now().toString());
          const fetchOptions = forceReload ? { cache: 'no-store' } : {};
          const res = await fetch(`/api/campaigns/${encodeURIComponent(campaignId)}?${params.toString()}`, fetchOptions);
          if (!res.ok) throw new Error('Failed to load campaign detail');
          const detail = await res.json();
          state.campaignDetail = detail;
          state.campaignFilters = state.campaignFilters || { route: 'all', placement: 'all', state: 'all' };
          updateViewVisibility();
          renderCampaignDetail();
        } catch (error) {
          console.error(error);
          showToast('Unable to load campaign detail', 'error');
          showCampaignList();
        }
      }

      function findCampaignVariant(detail, placementId, routeId, index) {
        if (!detail) return null;
        const cell = (detail.matrix || []).find((entry) => entry.placementId === placementId && entry.routeId === routeId);
        if (!cell) return null;
        return (cell.variants || []).find((variant) => Number(variant.index) === Number(index)) || null;
      }

      function openCampaignVariantOverlay(placementId, routeId, index) {
        const detail = state.campaignDetail;
        if (!detail) return;
        const cell = (detail.matrix || []).find((entry) => entry.placementId === placementId && entry.routeId === routeId) || {};
        const variants = cell.variants || [];
        const primaryIndex = Number(index);
        const primary = variants.find((variant) => Number(variant.index) === primaryIndex);
        if (!primary) return;
        const secondaryCandidate = variants.find((variant) => Number(variant.index) !== primaryIndex);
        state.activeCampaignVariant = {
          campaignId: state.selectedCampaignId,
          placementId,
          routeId,
          variants,
          primaryIndex,
          secondaryIndex: secondaryCandidate ? Number(secondaryCandidate.index) : null,
          initialPrimaryIndex: primaryIndex,
          initialSecondaryIndex: secondaryCandidate ? Number(secondaryCandidate.index) : null,
          originalSecondaryIndex: secondaryCandidate ? Number(secondaryCandidate.index) : null,
          originalState: primary.reviewState,
          originalNotes: (primary.notes || '').trim(),
        };
        campaignOverlayPrimary.innerHTML = variants
          .map((variant) => `<option value="${variant.index}">v${String(variant.index + 1).padStart(3, '0')} (${escapeHtml(variant.reviewState || 'pending')})</option>`)
          .join('');
        campaignOverlaySecondary.innerHTML = ['<option value="">None</option>']
          .concat(variants.map((variant) => `<option value="${variant.index}">v${String(variant.index + 1).padStart(3, '0')}</option>`))
          .join('');
        campaignOverlay.classList.remove('hidden');
        updateCampaignOverlayComparison();
      }

      function updateCampaignOverlayComparison() {
        const active = state.activeCampaignVariant;
        if (!active) return;
        const detail = state.campaignDetail || {};
        const placementMeta = (detail.placements || []).find((item) => item.placementId === active.placementId) || {};
        const routeMeta = (detail.routes || []).find((item) => item.routeId === active.routeId) || {};
        const variants = active.variants || [];
        const primary = variants.find((variant) => Number(variant.index) === Number(active.primaryIndex));
        if (!primary) return;
        const secondary = variants.find((variant) => Number(variant.index) === Number(active.secondaryIndex));

        campaignOverlayPrimary.value = String(active.primaryIndex);
        campaignOverlaySecondary.value = secondary ? String(secondary.index) : '';
        campaignOverlaySubtitle.innerHTML = `${escapeHtml(active.placementId)} • ${escapeHtml(routeMeta.name || active.routeId)}`;

        campaignOverlayState.value = primary.reviewState || 'pending';
        const originalNotes = (primary.notes || '').trim();
        if (active.notesOverride === undefined) {
          active.notesOverride = originalNotes;
        }
        campaignOverlayNotes.value = active.notesOverride || '';

        const previewA = primary.imageUrl || primary.thumbnailUrl || '';
        campaignOverlayImageA.src = previewA;
        campaignOverlayInfoA.innerHTML = `
          <div>Seed: ${escapeHtml(String(primary.seed ?? '—'))}</div>
          <div>${escapeHtml(formatTimestamp(primary.createdAt))}</div>
          <div style="word-break:break-word;">${escapeHtml(primary.prompt || '')}</div>
        `;

        if (secondary) {
          const previewB = secondary.imageUrl || secondary.thumbnailUrl || '';
          campaignOverlayImageB.src = previewB;
          campaignOverlayInfoB.innerHTML = `
            <div>Seed: ${escapeHtml(String(secondary.seed ?? '—'))}</div>
            <div>${escapeHtml(formatTimestamp(secondary.createdAt))}</div>
            <div style="word-break:break-word;">${escapeHtml(secondary.prompt || '')}</div>
          `;
        } else {
          campaignOverlayImageB.src = '';
          campaignOverlayInfoB.innerHTML = '<div style="color:var(--text-soft);">No comparison selected</div>';
        }

        campaignOverlayPromptDiff.innerHTML = renderPromptDiff(primary.prompt, secondary ? secondary.prompt : null);
        campaignOverlayTimeline.innerHTML = renderVariantTimeline(primary);
        campaignOverlayJson.textContent = JSON.stringify(primary, null, 2);

        active.currentPrimary = primary;
        active.currentSecondary = secondary || null;
        active.primaryOriginalState = active.originalState;
        active.primaryOriginalNotes = active.originalNotes;
      }

      function closeCampaignOverlay() {
        state.activeCampaignVariant = null;
        campaignOverlay.classList.add('hidden');
      }

      function resetCampaignOverlayInputs() {
        const active = state.activeCampaignVariant;
        if (!active) return;
        active.primaryIndex = Number(active.initialPrimaryIndex ?? active.primaryIndex);
        active.secondaryIndex = active.initialSecondaryIndex ?? null;
        active.notesOverride = active.originalNotes || '';
        campaignOverlayState.value = active.originalState || 'pending';
        updateCampaignOverlayComparison();
      }

      async function updateCampaignVariantState(placementId, routeId, variantIndex, nextState, notes) {
        if (!state.selectedCampaignId) throw new Error('No campaign selected');
        const params = new URLSearchParams();
        if (state.projectId) {
          params.set('project', state.projectId);
        }
        const payload = {
          placementId,
          routeId,
          variantIndex,
          state: nextState,
          notes,
        };
        const res = await fetch(`/api/campaigns/${encodeURIComponent(state.selectedCampaignId)}/review?${params.toString()}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload),
        });
        if (!res.ok) throw new Error('Review update failed');
        const data = await res.json();
        const detail = state.campaignDetail;
        if (detail) {
          const cell = (detail.matrix || []).find((entry) => entry.placementId === placementId && entry.routeId === routeId);
          if (cell) {
            const updated = (cell.variants || []).find((variant) => Number(variant.index) === Number(variantIndex));
            if (updated && data.variant) {
              Object.assign(updated, data.variant);
            }
          }
          const placement = (detail.placements || []).find((item) => item.placementId === placementId);
          if (placement && data.counts) {
            placement.counts = data.counts;
            placement.generatedVariants = (data.counts.approved ?? 0) + (data.counts.pending ?? 0) + (data.counts.revise ?? 0);
            placement.pendingVariants = data.counts.pending ?? placement.pendingVariants;
          }
          if (data.stats) {
            detail.stats = data.stats;
          }
        }
        const summary = state.campaigns.find((item) => item.campaignId === state.selectedCampaignId);
        if (summary && data.stats) {
          summary.approved = data.stats.approved ?? summary.approved;
          summary.pending = data.stats.pending ?? summary.pending;
          summary.revise = data.stats.revise ?? summary.revise;
          summary.variants = data.stats.total ?? summary.variants;
        }
        renderCampaignList();
        renderCampaignDetail();
        return data;
      }

      function buildFocusQueue(detail) {
        if (!detail) return [];
        const routeNames = new Map((detail.routes || []).map((route) => [route.routeId, route.name || route.routeId]));
        return (detail.matrix || [])
          .filter((cell) => Array.isArray(cell.variants) && cell.variants.length)
          .map((cell) => {
            const variants = cell.variants || [];
            const pending = variants.reduce(
              (count, variant) => count + (variant.reviewState === 'pending' ? 1 : 0),
              0,
            );
            return {
              placementId: cell.placementId,
              placementLabel: cell.placementId,
              routeId: cell.routeId,
              routeLabel: routeNames.get(cell.routeId) || cell.routeId,
              variants,
              pending,
            };
          })
          .sort((a, b) => {
            const aReady = a.pending === 0;
            const bReady = b.pending === 0;
            if (aReady !== bReady) {
              return aReady ? -1 : 1;
            }
            if (a.placementId !== b.placementId) {
              return a.placementId.localeCompare(b.placementId);
            }
            return a.routeId.localeCompare(b.routeId);
          });
      }

      function restoreFocusSelection(queue) {
        if (!queue.length) {
          return { placementIndex: -1, variantIndex: FOCUS_NEXT_SENTINEL };
        }
        const storedRaw = localStorage.getItem(FOCUS_STORAGE_KEY);
        let defaultPlacement = queue.findIndex((entry) => entry.pending === 0);
        if (defaultPlacement === -1) defaultPlacement = 0;
        let defaultVariant = Number(queue[defaultPlacement].variants[0]?.index ?? FOCUS_NEXT_SENTINEL);
        if (!storedRaw) {
          return { placementIndex: defaultPlacement, variantIndex: defaultVariant };
        }
        try {
          const stored = JSON.parse(storedRaw);
          if (!stored) {
            return { placementIndex: defaultPlacement, variantIndex: defaultVariant };
          }
          if (stored.projectId && stored.projectId !== state.projectId) {
            return { placementIndex: defaultPlacement, variantIndex: defaultVariant };
          }
          if (stored.campaignId && stored.campaignId !== state.selectedCampaignId) {
            return { placementIndex: defaultPlacement, variantIndex: defaultVariant };
          }
          const placementIndex = queue.findIndex(
            (entry) => entry.placementId === stored.placementId && entry.routeId === stored.routeId,
          );
          if (placementIndex === -1) {
            return { placementIndex: defaultPlacement, variantIndex: defaultVariant };
          }
          const entry = queue[placementIndex];
          const storedVariant = stored.variantIndex;
          if (storedVariant === null || storedVariant === undefined) {
            return { placementIndex, variantIndex: Number(entry.variants[0]?.index ?? FOCUS_NEXT_SENTINEL) };
          }
          const exists = entry.variants.some((variant) => Number(variant.index) === Number(storedVariant));
          return {
            placementIndex,
            variantIndex: exists ? Number(storedVariant) : Number(entry.variants[0]?.index ?? FOCUS_NEXT_SENTINEL),
          };
        } catch (error) {
          console.warn('Unable to restore focus mode state', error);
          return { placementIndex: defaultPlacement, variantIndex: defaultVariant };
        }
      }

      function persistFocusState() {
        const focusState = state.focusMode;
        if (!focusState || !focusState.active) return;
        const entry = focusState.queue[focusState.currentIndex];
        if (!entry) return;
        const payload = {
          projectId: state.projectId,
          campaignId: state.selectedCampaignId,
          placementId: entry.placementId,
          routeId: entry.routeId,
          variantIndex: focusState.selectedIndex === FOCUS_NEXT_SENTINEL ? null : focusState.selectedIndex,
          updatedAt: Date.now(),
        };
        try {
          localStorage.setItem(FOCUS_STORAGE_KEY, JSON.stringify(payload));
        } catch (error) {
          console.warn('Unable to persist focus mode state', error);
        }
      }

      function getFocusEntry() {
        const focusState = state.focusMode;
        if (!focusState || !focusState.queue.length) {
          return null;
        }
        return focusState.queue[focusState.currentIndex] || null;
      }

      function getFocusIndices(entry) {
        const base = (entry?.variants || []).map((variant) => Number(variant.index));
        base.push(FOCUS_NEXT_SENTINEL);
        return base;
      }

      function moveFocusSelection(offset) {
        const focusState = state.focusMode;
        const entry = getFocusEntry();
        if (!focusState || !entry) return;
        const indices = getFocusIndices(entry);
        if (!indices.length) return;
        let currentPosition = indices.findIndex((value) => value === focusState.selectedIndex);
        if (currentPosition === -1) {
          currentPosition = 0;
        }
        const nextPosition = (currentPosition + offset + indices.length) % indices.length;
        focusState.selectedIndex = indices[nextPosition];
        focusState.reviseOpen = false;
        renderFocusMode();
        persistFocusState();
      }

      function selectFocusVariant(nextIndex) {
        const focusState = state.focusMode;
        if (!focusState) return;
        focusState.selectedIndex = nextIndex;
        focusState.reviseOpen = false;
        renderFocusMode();
        persistFocusState();
      }

      function refreshFocusQueue() {
        if (!state.focusMode || !state.focusMode.active || !state.campaignDetail) return;
        const focusState = state.focusMode;
        const prevEntry = getFocusEntry();
        const prevPlacement = prevEntry ? prevEntry.placementId : null;
        const prevRoute = prevEntry ? prevEntry.routeId : null;
        const prevVariant = focusState.selectedIndex;
        const queue = buildFocusQueue(state.campaignDetail);
        focusState.queue = queue;
        if (!queue.length) {
          focusState.currentIndex = 0;
          focusState.selectedIndex = FOCUS_NEXT_SENTINEL;
          return;
        }
        let placementIndex = queue.findIndex((entry) => entry.placementId === prevPlacement && entry.routeId === prevRoute);
        if (placementIndex === -1) {
          const restored = restoreFocusSelection(queue);
          placementIndex = restored.placementIndex >= 0 ? restored.placementIndex : 0;
          focusState.selectedIndex = restored.variantIndex;
        } else {
          const entry = queue[placementIndex];
          const exists = entry.variants.some((variant) => Number(variant.index) === Number(prevVariant));
          focusState.selectedIndex = exists
            ? prevVariant
            : Number(entry.variants[0]?.index ?? FOCUS_NEXT_SENTINEL);
        }
        focusState.currentIndex = placementIndex;
      }

      function renderFocusStrip(entry, selectedIndex) {
        if (!focusStrip) return;
        if (!entry) {
          focusStrip.innerHTML = '';
          return;
        }
        const items = [];
        entry.variants.forEach((variant) => {
          const isSelected = Number(variant.index) === Number(selectedIndex);
          items.push(`
            <button class="focus-thumb" type="button" data-index="${variant.index}" data-state="${escapeHtml(variant.reviewState || 'pending')}" data-selected="${isSelected ? 'true' : 'false'}">
              ${variant.thumbnailUrl ? `<img src="${variant.thumbnailUrl}" alt="${escapeHtml(variant.variantId || '')}">` : '<span style="font-size:0.75rem;color:var(--text-soft);">No preview</span>'}
              <span class="status-chip">${escapeHtml(variant.reviewState || 'pending')}</span>
            </button>
          `);
        });
        const nextSelected = selectedIndex === FOCUS_NEXT_SENTINEL;
        items.push(`
          <button class="focus-thumb" type="button" data-kind="next" data-selected="${nextSelected ? 'true' : 'false'}">
            Next ▶
          </button>
        `);
        focusStrip.innerHTML = items.join('');
      }

      function renderFocusMode() {
        if (!state.focusMode || !state.focusMode.active) return;
        const entry = getFocusEntry();
        if (!entry) {
          focusTitle.textContent = 'Focus review';
          focusSubtitle.textContent = '';
          focusHeroImage.src = '';
          focusHeroImage.classList.add('hidden');
          focusHeroPlaceholder.classList.remove('hidden');
          renderFocusStrip(null, FOCUS_NEXT_SENTINEL);
          focusProgress.textContent = 'No variants available.';
          focusApproveBtn.disabled = true;
          focusReviseBtn.disabled = true;
          focusNotes.dataset.visible = 'false';
          return;
        }
        const focusState = state.focusMode;
        const selectedIndex = focusState.selectedIndex ?? Number(entry.variants[0]?.index ?? FOCUS_NEXT_SENTINEL);
        const placementPosition = `${focusState.currentIndex + 1}/${focusState.queue.length}`;
        const approvedCount = entry.variants.filter((variant) => variant.reviewState === 'approved').length;
        const pendingCount = entry.variants.filter((variant) => variant.reviewState === 'pending').length;
        focusTitle.textContent = `${entry.placementLabel}`;
        focusSubtitle.textContent = `${entry.routeLabel}`;
        focusProgress.textContent = `Placement ${placementPosition} • Approved ${approvedCount} • Pending ${pendingCount}`;

        renderFocusStrip(entry, selectedIndex);

        if (selectedIndex === FOCUS_NEXT_SENTINEL) {
          focusHeroImage.src = '';
          focusHeroImage.classList.add('hidden');
          focusHeroPlaceholder.textContent = 'Ready for next placement';
          focusHeroPlaceholder.classList.remove('hidden');
          focusApproveBtn.disabled = false;
          focusApproveBtn.textContent = 'Next placement ▲';
          focusReviseBtn.disabled = true;
          focusNotes.dataset.visible = 'false';
        } else {
          const variant = entry.variants.find((item) => Number(item.index) === Number(selectedIndex));
          const preview = variant ? (variant.imageUrl || variant.thumbnailUrl || '') : '';
          if (preview) {
            focusHeroImage.src = preview;
            focusHeroImage.classList.remove('hidden');
            focusHeroPlaceholder.classList.add('hidden');
          } else {
            focusHeroImage.src = '';
            focusHeroImage.classList.add('hidden');
            focusHeroPlaceholder.textContent = 'Preview unavailable';
            focusHeroPlaceholder.classList.remove('hidden');
          }
          focusApproveBtn.disabled = !!focusState.busy;
          focusApproveBtn.textContent = 'Approve ▲';
          focusReviseBtn.disabled = !!focusState.busy;
          if (focusState.reviseOpen) {
            focusNotes.dataset.visible = 'true';
            if (focusNotesInput && variant) {
              focusNotesInput.value = variant.notes || '';
            }
          } else {
            focusNotes.dataset.visible = 'false';
          }
        }
      }

      function handleFocusKeydown(event) {
        if (!state.focusMode || !state.focusMode.active) return;
        if (event.key === 'Escape') {
          event.preventDefault();
          closeFocusMode();
          return;
        }
        if (event.target && ['TEXTAREA', 'INPUT'].includes(event.target.tagName)) {
          return;
        }
        switch (event.key) {
          case 'ArrowLeft':
            event.preventDefault();
            moveFocusSelection(-1);
            break;
          case 'ArrowRight':
            event.preventDefault();
            moveFocusSelection(1);
            break;
          case 'ArrowUp':
            event.preventDefault();
            if (state.focusMode.selectedIndex === FOCUS_NEXT_SENTINEL) {
              advanceFocusPlacement();
            } else {
              focusApproveCurrent();
            }
            break;
          case 'ArrowDown':
            event.preventDefault();
            if (state.focusMode.selectedIndex === FOCUS_NEXT_SENTINEL) {
              return;
            }
            if (state.focusMode.reviseOpen) {
              focusSubmitRevision();
            } else {
              focusEnterRevise();
            }
            break;
          default:
            break;
        }
      }

      function openFocusMode() {
        const detail = state.campaignDetail;
        if (!detail) return;
        const queue = buildFocusQueue(detail);
        if (!queue.length) {
          showToast('No variants ready for focus review', 'info');
          return;
        }
        const restored = restoreFocusSelection(queue);
        const placementIndex = restored.placementIndex >= 0 ? restored.placementIndex : 0;
        const variantIndex = restored.variantIndex ?? Number(queue[placementIndex].variants[0]?.index ?? FOCUS_NEXT_SENTINEL);
        state.focusMode = {
          active: true,
          queue,
          currentIndex: placementIndex,
          selectedIndex: variantIndex,
          reviseOpen: false,
          busy: false,
        };
        persistFocusState();
        if (focusNotes) {
          focusNotes.dataset.visible = 'false';
        }
        if (focusKeyHandler) {
          window.removeEventListener('keydown', focusKeyHandler, true);
        }
        focusKeyHandler = (event) => handleFocusKeydown(event);
        window.addEventListener('keydown', focusKeyHandler, true);
        focusOverlay.classList.remove('hidden');
        renderFocusMode();
      }

      function closeFocusMode() {
        if (focusKeyHandler) {
          window.removeEventListener('keydown', focusKeyHandler, true);
          focusKeyHandler = null;
        }
        persistFocusState();
        focusOverlay.classList.add('hidden');
        state.focusMode = null;
        focusNotes.dataset.visible = 'false';
      }

      async function focusApproveCurrent() {
        const focusState = state.focusMode;
        const entry = getFocusEntry();
        if (!focusState || !entry || focusState.busy) return;
        if (focusState.selectedIndex === FOCUS_NEXT_SENTINEL) {
          advanceFocusPlacement();
          return;
        }
        const variant = entry.variants.find((item) => Number(item.index) === Number(focusState.selectedIndex));
        if (!variant) return;
        try {
          focusState.busy = true;
          focusApproveBtn.disabled = true;
          focusReviseBtn.disabled = true;
          await updateCampaignVariantState(entry.placementId, entry.routeId, variant.index, 'approved', '');
          focusState.reviseOpen = false;
          refreshFocusQueue();
          renderFocusMode();
          showToast('Approved variant');
          persistFocusState();
        } catch (error) {
          console.error(error);
          showToast('Unable to approve variant', 'error');
        } finally {
          if (focusState) {
            focusState.busy = false;
          }
          renderFocusMode();
        }
      }

      function focusEnterRevise() {
        const focusState = state.focusMode;
        const entry = getFocusEntry();
        if (!focusState || !entry) return;
        if (focusState.selectedIndex === FOCUS_NEXT_SENTINEL) return;
        const variant = entry.variants.find((item) => Number(item.index) === Number(focusState.selectedIndex));
        if (!variant) return;
        focusState.reviseOpen = true;
        focusNotes.dataset.visible = 'true';
        if (focusNotesInput) {
          focusNotesInput.value = variant.notes || '';
          focusNotesInput.focus();
          focusNotesInput.select();
        }
        renderFocusMode();
      }

      async function focusSubmitRevision() {
        const focusState = state.focusMode;
        const entry = getFocusEntry();
        if (!focusState || !entry || focusState.busy) return;
        if (focusState.selectedIndex === FOCUS_NEXT_SENTINEL) return;
        const variant = entry.variants.find((item) => Number(item.index) === Number(focusState.selectedIndex));
        if (!variant) return;
        const notes = (focusNotesInput?.value || '').trim();
        try {
          focusState.busy = true;
          focusApproveBtn.disabled = true;
          focusReviseBtn.disabled = true;
          await updateCampaignVariantState(entry.placementId, entry.routeId, variant.index, 'revise', notes);
          focusState.reviseOpen = false;
          refreshFocusQueue();
          renderFocusMode();
          showToast('Requested revision');
          persistFocusState();
        } catch (error) {
          console.error(error);
          showToast('Unable to request revision', 'error');
        } finally {
          if (focusState) {
            focusState.busy = false;
          }
          renderFocusMode();
        }
      }

      function advanceFocusPlacement() {
        const focusState = state.focusMode;
        if (!focusState || !focusState.queue.length) return;
        focusState.reviseOpen = false;
        focusNotes.dataset.visible = 'false';
        focusState.currentIndex = (focusState.currentIndex + 1) % focusState.queue.length;
        const entry = getFocusEntry();
        focusState.selectedIndex = Number(entry?.variants[0]?.index ?? FOCUS_NEXT_SENTINEL);
        renderFocusMode();
        persistFocusState();
      }

      function openBlitzMode() {
        const detail = state.campaignDetail;
        if (!detail) return;
        if (!Array.isArray(detail.matrix) || !detail.matrix.some((cell) => (cell.variants || []).length)) {
          showToast('No variants to review yet', 'info');
          return;
        }
        const filterState = blitzFilterState ? blitzFilterState.value : 'all';
        state.blitzMode = {
          active: true,
          filterState,
          activeTile: null,
        };
        if (blitzFilterState) {
          blitzFilterState.value = filterState;
        }
        renderBlitzMode();
        if (blitzKeyHandler) {
          window.removeEventListener('keydown', blitzKeyHandler, true);
        }
        blitzKeyHandler = (event) => handleBlitzKeydown(event);
        window.addEventListener('keydown', blitzKeyHandler, true);
        blitzOverlay.classList.remove('hidden');
      }

      function closeBlitzMode() {
        blitzOverlay.classList.add('hidden');
        if (blitzKeyHandler) {
          window.removeEventListener('keydown', blitzKeyHandler, true);
          blitzKeyHandler = null;
        }
        state.blitzMode = null;
      }

      function collectBlitzGroups(detail, filterState) {
        const groups = new Map();
        const routeNames = new Map((detail.routes || []).map((route) => [route.routeId, route.name || route.routeId]));
        (detail.matrix || []).forEach((cell) => {
          const variants = cell.variants || [];
          if (!variants.length) return;
          const placementId = cell.placementId;
          const routeId = cell.routeId;
          let group = groups.get(placementId);
          if (!group) {
            group = {
              placementId,
              variants: [],
            };
            groups.set(placementId, group);
          }
          variants.forEach((variant) => {
            const stateKey = variant.reviewState || 'pending';
            if (filterState !== 'all' && stateKey !== filterState) return;
            group.variants.push({
              placementId,
              routeId,
              routeLabel: routeNames.get(routeId) || routeId,
              index: variant.index,
              imageUrl: variant.imageUrl || variant.thumbnailUrl || '',
              reviewState: stateKey,
              label: variant.variantId || `v${String(Number(variant.index) + 1).padStart(3, '0')}`,
              createdAt: variant.createdAt,
            });
          });
        });
        const ordered = Array.from(groups.values()).sort((a, b) => a.placementId.localeCompare(b.placementId));
        ordered.forEach((group) => {
          group.variants.sort((a, b) => {
            if (a.createdAt && b.createdAt) {
              return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime();
            }
            return 0;
          });
        });
        return ordered;
      }

      function renderBlitzMode() {
        if (!state.blitzMode || !state.campaignDetail) return;
        const detail = state.campaignDetail;
        const filterState = state.blitzMode.filterState || 'all';
        if (blitzFilterState) {
          blitzFilterState.value = filterState;
        }
        const groups = collectBlitzGroups(detail, filterState);
        const stats = detail.stats || {};
        if (blitzApprovedCount) blitzApprovedCount.textContent = stats.approved ?? 0;
        if (blitzPendingCount) blitzPendingCount.textContent = stats.pending ?? 0;
        if (blitzReviseCount) blitzReviseCount.textContent = stats.revise ?? 0;
        if (blitzTitle) {
          blitzTitle.textContent = detail.campaign?.name ? `${detail.campaign.name} · Blitz` : 'Variant blitz';
        }
        if (blitzSubtitle) {
          blitzSubtitle.textContent = `${groups.length} placement${groups.length === 1 ? '' : 's'} grouped by placement`;
        }
        if (!blitzContent) return;
        if (!groups.length) {
          blitzContent.innerHTML = '<div class="blitz-empty">No variants match the current filter.</div>';
          return;
        }
        const active = state.blitzMode.activeTile;
        const sections = groups.map((group) => {
          const tiles = group.variants.map((variant) => {
            const isActive = active
              && active.placementId === variant.placementId
              && active.routeId === variant.routeId
              && Number(active.index) === Number(variant.index);
            const badge = escapeHtml(variant.routeLabel);
            const stateKey = escapeHtml(variant.reviewState || 'pending');
            const meta = escapeHtml(variant.label);
            return `
              <button class="blitz-tile" type="button" data-placement="${escapeHtml(variant.placementId)}" data-route="${escapeHtml(variant.routeId)}" data-index="${variant.index}" data-state="${escapeHtml(variant.reviewState || 'pending')}" data-active="${isActive ? 'true' : 'false'}">
                ${variant.imageUrl ? `<img src="${variant.imageUrl}" alt="${meta} preview">` : '<span style="font-size:0.8rem;color:var(--text-soft);">No image</span>'}
                <span class="tile-badge">${badge}</span>
                <div class="tile-meta"><span>${meta}</span><span>${stateKey}</span></div>
              </button>
            `;
          }).join('');
          return `
            <section class="blitz-placement">
              <header>
                <h3>${escapeHtml(group.placementId)}</h3>
                <span style="font-size:0.78rem;color:var(--text-soft);">${group.variants.length} variant${group.variants.length === 1 ? '' : 's'}</span>
              </header>
              <div class="blitz-grid">
                ${tiles || '<div class="blitz-empty">No variants match this filter.</div>'}
              </div>
            </section>
          `;
        });
        blitzContent.innerHTML = sections.join('');
      }

      async function setBlitzVariantState(placementId, routeId, variantIndex, nextState, notes) {
        try {
          await updateCampaignVariantState(placementId, routeId, variantIndex, nextState, notes ?? '');
          renderBlitzMode();
          renderFocusMode();
          if (nextState === 'approved') {
            showToast('Approved variant');
          } else if (nextState === 'revise') {
            showToast('Requested revision');
          } else {
            showToast('Marked pending');
          }
        } catch (error) {
          console.error(error);
          showToast('Unable to update variant state', 'error');
        }
      }

      function cycleBlitzVariant(tile, shiftKey) {
        if (!tile || !state.campaignDetail) return;
        const placementId = tile.dataset.placement;
        const routeId = tile.dataset.route;
        const variantIndex = Number(tile.dataset.index);
        const currentState = tile.dataset.state || 'pending';
        state.blitzMode.activeTile = { placementId, routeId, index: variantIndex };
        let nextState;
        let notes = '';
        if (shiftKey) {
          nextState = 'revise';
          notes = window.prompt('Revision notes (optional):', '') || '';
        } else {
          if (currentState === 'approved') {
            nextState = 'pending';
          } else {
            nextState = 'approved';
          }
        }
        setBlitzVariantState(placementId, routeId, variantIndex, nextState, notes);
      }

      function handleBlitzKeydown(event) {
        if (!state.blitzMode || !state.blitzMode.active) return;
        if (event.key === 'Escape') {
          event.preventDefault();
          closeBlitzMode();
          return;
        }
        if (!state.blitzMode.activeTile) return;
        const { placementId, routeId, index } = state.blitzMode.activeTile;
        switch (event.key.toLowerCase()) {
          case 'a':
            event.preventDefault();
            setBlitzVariantState(placementId, routeId, index, 'approved', '');
            break;
          case 'r':
            event.preventDefault();
            {
              const notes = window.prompt('Revision notes (optional):', '') || '';
              setBlitzVariantState(placementId, routeId, index, 'revise', notes);
            }
            break;
          case 'p':
            event.preventDefault();
            setBlitzVariantState(placementId, routeId, index, 'pending', '');
            break;
          default:
            break;
        }
      }

      async function submitCampaignReview() {
        const active = state.activeCampaignVariant;
        if (!active || !state.selectedCampaignId) return;
        const primary = active.currentPrimary;
        if (!primary) return;
        try {
          const nextState = campaignOverlayState.value || 'pending';
          const nextNotes = (campaignOverlayNotes.value || '').trim();
          if (nextState === (active.primaryOriginalState || 'pending') && nextNotes === (active.primaryOriginalNotes || '')) {
            closeCampaignOverlay();
            return;
          }
          if (campaignOverlayApply) {
            campaignOverlayApply.disabled = true;
          }
          const data = await updateCampaignVariantState(active.placementId, active.routeId, primary.index, nextState, nextNotes);
          active.originalState = nextState;
          active.originalNotes = nextNotes;
          active.notesOverride = nextNotes;
          showToast('Review updated');
          closeCampaignOverlay();
        } catch (error) {
          console.error(error);
          showToast('Unable to update review state', 'error');
        } finally {
          if (campaignOverlayApply) {
            campaignOverlayApply.disabled = false;
          }
        }
      }

      function renderPromptDiff(promptA, promptB) {
        if (!promptB || promptA === promptB) {
          return `<div><strong>Prompt</strong><br>${escapeHtml(promptA || 'No prompt')}</div>`;
        }
        const wordsA = new Set((promptA || '').split(/\s+/).filter(Boolean));
        const wordsB = new Set((promptB || '').split(/\s+/).filter(Boolean));
        const adds = [...wordsB].filter((word) => !wordsA.has(word));
        const removes = [...wordsA].filter((word) => !wordsB.has(word));
        return `
          <div><strong>Prompt A</strong><br>${escapeHtml(promptA || '')}</div>
          <div><strong>Prompt B</strong><br>${escapeHtml(promptB || '')}</div>
          <div class="campaign-card-meta">
            ${adds.length ? `<span class="diff-add">+ ${escapeHtml(adds.join(' '))}</span>` : ''}
            ${removes.length ? `<span class="diff-remove">- ${escapeHtml(removes.join(' '))}</span>` : ''}
          </div>
        `;
      }

      function renderVariantTimeline(variant) {
        const events = [];
        events.push(`
          <div class="timeline-entry">
            <span>🗓</span>
            <div><strong>Generated</strong><br>${escapeHtml(formatTimestamp(variant.createdAt))}</div>
          </div>
        `);
        if (variant.reviewState) {
          events.push(`
            <div class="timeline-entry">
              <span>✅</span>
              <div><strong>Review state</strong><br>${escapeHtml(variant.reviewState)}</div>
            </div>
          `);
        }
        return events.join('');
      }

      slotGrid.addEventListener('click', (event) => {
        const card = event.target.closest('.slot-card');
        if (!card) return;
        const slotId = card.dataset.slot;
        if (slotId) {
          selectSlot(slotId).catch((error) => console.error(error));
        }
      });

      sessionList.addEventListener('click', (event) => {
        const button = event.target.closest('.session-item');
        if (!button) return;
        const sessionId = button.dataset.session;
        state.sessionFilter = sessionId && sessionId !== '__all__' ? sessionId : null;
        renderSessionList();
        renderSessionSummary();
        renderVariantFeed();
      });

      variantGrid.addEventListener('click', (event) => {
        const button = event.target.closest('button');
        if (!button) return;
        const action = button.dataset.action;
        const sessionId = button.dataset.session;
        const index = button.dataset.index;
        if (!sessionId || index === undefined) return;
        if (action === 'metadata') {
          openMetadata(sessionId, index);
        } else if (action === 'promote') {
          promoteVariant(sessionId, index);
        } else if (action === 'open-raw') {
          const variant = getVariant(sessionId, index);
          if (variant && variant.raw && variant.raw.url) {
            window.open(variant.raw.url, '_blank');
          }
        }
      });

      reviewModeCards.forEach((card) => {
        card.addEventListener('click', () => {
          const mode = card.dataset.mode;
          if (mode === 'focus') {
            openFocusMode();
          } else if (mode === 'blitz') {
            openBlitzMode();
          }
        });
      });

      if (focusStrip) {
        focusStrip.addEventListener('click', (event) => {
          const thumb = event.target.closest('.focus-thumb');
          if (!thumb || !state.focusMode) return;
          const kind = thumb.dataset.kind;
          const nextIndex = kind === 'next' ? FOCUS_NEXT_SENTINEL : Number(thumb.dataset.index);
          selectFocusVariant(nextIndex);
        });
      }

      if (focusApproveBtn) {
        focusApproveBtn.addEventListener('click', () => {
          if (!state.focusMode) return;
          if (state.focusMode.selectedIndex === FOCUS_NEXT_SENTINEL) {
            advanceFocusPlacement();
          } else {
            focusApproveCurrent();
          }
        });
      }

      if (focusReviseBtn) {
        focusReviseBtn.addEventListener('click', () => {
          if (!state.focusMode || state.focusMode.selectedIndex === FOCUS_NEXT_SENTINEL) return;
          if (state.focusMode.reviseOpen) {
            focusSubmitRevision();
          } else {
            focusEnterRevise();
          }
        });
      }

      if (focusNotesCancel) {
        focusNotesCancel.addEventListener('click', () => {
          if (!state.focusMode) return;
          state.focusMode.reviseOpen = false;
          focusNotes.dataset.visible = 'false';
        });
      }

      if (focusNotesSave) {
        focusNotesSave.addEventListener('click', () => {
          focusSubmitRevision();
        });
      }

      if (focusClose) {
        focusClose.addEventListener('click', () => {
          closeFocusMode();
        });
      }

      if (blitzFilterState) {
        blitzFilterState.addEventListener('change', (event) => {
          if (!state.blitzMode) return;
          state.blitzMode.filterState = event.target.value;
          renderBlitzMode();
        });
      }

      if (blitzContent) {
        blitzContent.addEventListener('click', (event) => {
          const tile = event.target.closest('.blitz-tile');
          if (!tile) return;
          if (state.blitzMode) {
            state.blitzMode.activeTile = {
              placementId: tile.dataset.placement,
              routeId: tile.dataset.route,
              index: Number(tile.dataset.index),
            };
          }
          blitzContent.querySelectorAll('.blitz-tile[data-active="true"]').forEach((el) => {
            if (el !== tile) el.dataset.active = 'false';
          });
          tile.dataset.active = 'true';
          cycleBlitzVariant(tile, event.shiftKey);
        });
        blitzContent.addEventListener('focusin', (event) => {
          const tile = event.target.closest('.blitz-tile');
          if (!tile || !state.blitzMode) return;
          state.blitzMode.activeTile = {
            placementId: tile.dataset.placement,
            routeId: tile.dataset.route,
            index: Number(tile.dataset.index),
          };
          blitzContent.querySelectorAll('.blitz-tile[data-active="true"]').forEach((el) => {
            if (el !== tile) el.dataset.active = 'false';
          });
          tile.dataset.active = 'true';
        });
      }

      if (blitzClose) {
        blitzClose.addEventListener('click', () => {
          closeBlitzMode();
        });
      }

      if (projectSelect) {
        projectSelect.addEventListener('change', (event) => {
          const nextProject = event.target.value;
          if (!nextProject || nextProject === state.projectId) {
            return;
          }
          state.pendingSlot = null;
          setProject(nextProject);
        });
      }

      refreshSlotsBtn.addEventListener('click', () => {
        loadSlots({ forceReload: true });
      });

      refreshSlotBtn.addEventListener('click', async () => {
        if (state.slot) {
          await loadSlotData(state.slot, { forceReload: true, preserveFilter: true });
          await loadSlots({ forceReload: true });
        }
      });

      filterWarningsBtn.addEventListener('click', () => {
        state.filterWarnings = !state.filterWarnings;
        renderSlots();
      });

      backToSlotsBtn.addEventListener('click', () => {
        resetSlotView();
        updateUrlState();
        loadSlots();
      });

      openSelectedBtn.addEventListener('click', () => {
        const url = openSelectedBtn.dataset.url;
        if (url) {
          window.open(url, '_blank');
        }
      });

      if (deleteSlotBtn) {
        deleteSlotBtn.addEventListener('click', () => {
          if (!state.slot) {
            return;
          }
          const message = `Delete slot "${state.slot}"? This removes all sessions and the selected image.`;
          const confirmed = window.confirm(message);
          if (!confirmed) {
            deleteSlotBtn.blur();
            return;
          }
          requestSlotDeletion(state.slot).catch((error) => console.error(error));
        });
      }

      if (tabSlots) {
        tabSlots.addEventListener('click', () => {
          setViewMode('slots');
        });
      }

      if (tabCampaigns) {
        tabCampaigns.addEventListener('click', () => {
          setViewMode('campaigns');
          showCampaignList();
        });
      }

      if (refreshCampaignsBtn) {
        refreshCampaignsBtn.addEventListener('click', () => {
          loadCampaigns({ forceReload: true });
        });
      }

      if (campaignSearchInput) {
        campaignSearchInput.addEventListener('input', (event) => {
          state.campaignSearch = (event.target.value || '').toString();
          renderCampaignList();
        });
      }

      if (campaignStatusFilter) {
        campaignStatusFilter.addEventListener('change', (event) => {
          state.campaignStatusFilter = event.target.value || 'all';
          renderCampaignList();
        });
      }

      async function handleCampaignAction(action, campaignId) {
        if (!campaignId) return;
        try {
          if (action === 'open') {
            await selectCampaign(campaignId);
          } else if (action === 'status') {
            await selectCampaign(campaignId);
            const detail = state.campaignDetail;
            if (detail && detail.statusReport) {
              await navigator.clipboard.writeText(JSON.stringify(detail.statusReport, null, 2));
              showToast('Status JSON copied');
            } else {
              showToast('Status unavailable', 'error');
            }
          } else if (action === 'resume') {
            await selectCampaign(campaignId);
            const detail = state.campaignDetail;
            const resume = detail && detail.resume;
            if (resume && resume.placementId && resume.routeId !== undefined && resume.variantIndex !== undefined) {
              openCampaignVariantOverlay(resume.placementId, resume.routeId, resume.variantIndex);
            } else {
              showToast('No pending variants to resume', 'info');
            }
          }
        } catch (error) {
          console.error(error);
          showToast('Unable to process campaign action', 'error');
        }
      }

      if (campaignSummaryGrid) {
        campaignSummaryGrid.addEventListener('click', (event) => {
          const actionButton = event.target.closest('button[data-action]');
          if (actionButton) {
            const action = actionButton.dataset.action;
            const campaignId = actionButton.dataset.campaign;
            if (action) {
              handleCampaignAction(action, campaignId);
            }
            return;
          }
          const card = event.target.closest('.campaign-card');
          if (card) {
            const campaignId = card.dataset.campaign;
            if (campaignId) {
              selectCampaign(campaignId).catch((error) => console.error(error));
            }
          }
        });
      }

      if (campaignQuickActions) {
        campaignQuickActions.addEventListener('click', (event) => {
          const button = event.target.closest('button[data-action]');
          if (!button) return;
          const action = button.dataset.action;
          const campaignId = button.dataset.campaign;
          handleCampaignAction(action, campaignId);
        });
      }

      if (campaignAlertsPanel) {
        campaignAlertsPanel.addEventListener('click', (event) => {
          const alertItem = event.target.closest('.alert-item[data-campaign]');
          if (!alertItem) return;
          const campaignId = alertItem.dataset.campaign;
          handleCampaignAction('open', campaignId);
        });
      }

      if (campaignFilterRoute) {
        campaignFilterRoute.addEventListener('change', (event) => {
          state.campaignFilters.route = event.target.value || 'all';
          renderCampaignDetail();
        });
      }

      if (campaignRouteList) {
        campaignRouteList.addEventListener('click', (event) => {
          const card = event.target.closest('.campaign-route-card');
          if (!card) return;
          const routeId = card.dataset.route;
          if (!routeId) return;
          state.campaignFilters.route = state.campaignFilters.route === routeId ? 'all' : routeId;
          renderCampaignDetail();
        });
      }

      if (campaignFilterPlacement) {
        campaignFilterPlacement.addEventListener('change', (event) => {
          state.campaignFilters.placement = event.target.value || 'all';
          renderCampaignDetail();
        });
      }

      if (campaignFilterState) {
        campaignFilterState.addEventListener('change', (event) => {
          state.campaignFilters.state = event.target.value || 'all';
          renderCampaignDetail();
        });
      }

      if (backToCampaignsBtn) {
        backToCampaignsBtn.addEventListener('click', () => {
          showCampaignList();
        });
      }

      if (refreshCampaignDetailBtn) {
        refreshCampaignDetailBtn.addEventListener('click', () => {
          if (state.selectedCampaignId) {
            loadCampaignDetail(state.selectedCampaignId, { forceReload: true });
          }
        });
      }

      if (campaignCopyStatusBtn) {
        campaignCopyStatusBtn.addEventListener('click', async () => {
          const detail = state.campaignDetail;
          if (detail && detail.statusReport) {
            try {
              await navigator.clipboard.writeText(JSON.stringify(detail.statusReport, null, 2));
              showToast('Status JSON copied');
            } catch (error) {
              console.error(error);
              showToast('Unable to copy status JSON', 'error');
            }
          } else {
            showToast('Load a campaign first to copy status', 'info');
          }
        });
      }

      if (campaignGrid) {
        campaignGrid.addEventListener('click', (event) => {
          const thumb = event.target.closest('.campaign-variant-thumb');
          if (!thumb) return;
          const placementId = thumb.dataset.placement;
          const routeId = thumb.dataset.route;
          const index = thumb.dataset.index;
          if (!placementId || !routeId || index === undefined) return;
          openCampaignVariantOverlay(placementId, routeId, Number(index));
        });
      }

      if (campaignOverlayClose) {
        campaignOverlayClose.addEventListener('click', () => {
          closeCampaignOverlay();
        });
      }

      if (campaignOverlayPrimary) {
        campaignOverlayPrimary.addEventListener('change', (event) => {
          const active = state.activeCampaignVariant;
          if (!active) return;
          active.primaryIndex = Number(event.target.value);
          const variant = (active.variants || []).find((item) => Number(item.index) === Number(active.primaryIndex));
          if (variant) {
            active.originalState = variant.reviewState;
            active.originalNotes = (variant.notes || '').trim();
            active.notesOverride = (variant.notes || '').trim();
          }
          updateCampaignOverlayComparison();
        });
      }

      if (campaignOverlaySecondary) {
        campaignOverlaySecondary.addEventListener('change', (event) => {
          const active = state.activeCampaignVariant;
          if (!active) return;
          const value = event.target.value;
          active.secondaryIndex = value === '' ? null : Number(value);
          updateCampaignOverlayComparison();
        });
      }

      if (campaignOverlayNotes) {
        campaignOverlayNotes.addEventListener('input', (event) => {
          const active = state.activeCampaignVariant;
          if (!active) return;
          active.notesOverride = event.target.value;
        });
      }

      if (campaignOverlayDownload) {
        campaignOverlayDownload.addEventListener('click', () => {
          const active = state.activeCampaignVariant;
          const primary = active && active.currentPrimary;
          if (primary && primary.imageUrl) {
            window.open(primary.imageUrl, '_blank');
          }
        });
      }

      if (campaignOverlayOpen) {
        campaignOverlayOpen.addEventListener('click', () => {
          const active = state.activeCampaignVariant;
          const primary = active && active.currentPrimary;
          if (primary && primary.imageUrl) {
            window.open(primary.imageUrl, '_blank');
          }
        });
      }

      if (campaignOverlayCopyJson) {
        campaignOverlayCopyJson.addEventListener('click', async () => {
          const active = state.activeCampaignVariant;
          const primary = active && active.currentPrimary;
          if (!primary) return;
          try {
            await navigator.clipboard.writeText(JSON.stringify(primary, null, 2));
            showToast('Variant JSON copied');
          } catch (error) {
            console.error(error);
            showToast('Unable to copy JSON', 'error');
          }
        });
      }

      if (campaignOverlayCopyCommand) {
        campaignOverlayCopyCommand.addEventListener('click', async () => {
          const active = state.activeCampaignVariant;
          if (!active) return;
          const command = `imgen campaign generate ${active.campaignId} --placements ${active.placementId} --routes ${active.routeId} --variants 1`;
          try {
            await navigator.clipboard.writeText(command);
            showToast('Regenerate command copied');
          } catch (error) {
            console.error(error);
            showToast('Unable to copy command', 'error');
          }
        });
      }

      if (campaignOverlayReset) {
        campaignOverlayReset.addEventListener('click', () => {
          resetCampaignOverlayInputs();
        });
      }

      if (campaignOverlayApply) {
        campaignOverlayApply.addEventListener('click', () => {
          submitCampaignReview();
        });
      }

      if (campaignOverlay) {
        campaignOverlay.addEventListener('click', (event) => {
          if (event.target === campaignOverlay) {
            closeCampaignOverlay();
          }
        });
      }

      metadataCloseBtn.addEventListener('click', closeMetadata);
      metadataOverlay.addEventListener('click', (event) => {
        if (event.target === metadataOverlay) {
          closeMetadata();
        }
      });

      updateViewVisibility();
      loadProjects();
    })();
  </script>
</body>
</html>
"""


__all__ = ["serve_gallery", "GalleryServer"]
