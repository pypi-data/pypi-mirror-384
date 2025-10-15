"""Campaign status aggregation utilities."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from pydantic import BaseModel, ConfigDict, Field

from .schemas import CampaignConfig, CampaignRoute, PlacementManifest
from .workspace import CampaignWorkspace


_VARIANT_PATTERN = re.compile(r"^v(?P<index>\d{3})\.(?P<ext>[a-z0-9]+)$", re.IGNORECASE)


@dataclass(slots=True)
class PendingVariant:
    route_id: str
    placement_id: str
    variant_index: int


@dataclass(slots=True)
class RoutePlacementStatus:
    placement_id: str
    expected_variants: int
    generated_variants: int
    pending_variants: List[int] = field(default_factory=list)
    extra_generated: List[int] = field(default_factory=list)
    manifest_recorded: int = 0
    manifest_missing: List[int] = field(default_factory=list)
    next_variant_index: Optional[int] = None


@dataclass(slots=True)
class RouteStatus:
    route_id: str
    placements: List[RoutePlacementStatus]
    total_expected: int
    total_generated: int
    total_pending: int


@dataclass(slots=True)
class PlacementStatus:
    placement_id: str
    template_id: Optional[str]
    expected_variants: int
    generated_variants: int
    pending_variants: int
    extra_generated: int
    routes_with_output: int
    routes_missing: List[str] = field(default_factory=list)
    manifest_present: bool = False
    manifest_path: Optional[str] = None
    manifest_routes: int = 0


@dataclass(slots=True)
class CampaignTotals:
    routes: int
    placements: int
    expected_variants: int
    generated_variants: int
    pending_variants: int
    extra_generated: int


@dataclass(slots=True)
class CampaignStatusReport:
    campaign_id: str
    totals: CampaignTotals
    routes: List[RouteStatus]
    placements: List[PlacementStatus]
    pending: List[PendingVariant]
    orphan_files: List[str]
    missing_manifests: List[str]

    def to_dict(self) -> Dict[str, object]:
        """Return the report as a plain dictionary for serialization."""
        return {
            "campaign_id": self.campaign_id,
            "totals": asdict(self.totals),
            "routes": [asdict(route) for route in self.routes],
            "placements": [asdict(placement) for placement in self.placements],
            "pending": [asdict(item) for item in self.pending],
            "orphan_files": list(self.orphan_files),
            "missing_manifests": list(self.missing_manifests),
        }


@dataclass(slots=True)
class _PlacementInfo:
    placement_id: str
    template_id: Optional[str]
    expected_variants: Optional[int]


@dataclass(slots=True)
class _PlacementAccumulator:
    template_id: Optional[str] = None
    expected_total: int = 0
    generated_total: int = 0
    pending_total: int = 0
    extra_total: int = 0
    routes_with_output: set[str] = field(default_factory=set)
    routes_missing: set[str] = field(default_factory=set)
    manifest_present: bool = False
    manifest_path: Optional[str] = None
    manifest_routes: int = 0


def _build_placement_lookup(config: CampaignConfig) -> Dict[str, _PlacementInfo]:
    """Build placement expectations from config."""

    lookup: Dict[str, _PlacementInfo] = {}
    default_variants = config.variant_defaults.count

    for placement in config.placements:
        placement_id = placement.override_id or placement.template_id
        expected = placement.variants if placement.variants is not None else default_variants
        info = lookup.get(placement_id)
        if info is None:
            lookup[placement_id] = _PlacementInfo(
                placement_id=placement_id,
                template_id=placement.template_id,
                expected_variants=expected,
            )
        else:
            # Prefer the largest expectation if duplicates exist.
            info.expected_variants = max(info.expected_variants or 0, expected)
            if not info.template_id:
                info.template_id = placement.template_id

    return lookup


def _include_ondisk_placements(lookup: Dict[str, _PlacementInfo], workspace: CampaignWorkspace, routes: Sequence[CampaignRoute]) -> None:
    for route in routes:
        route_dir = workspace.images_dir / route.route_id
        if not route_dir.exists():
            continue
        for candidate in sorted(route_dir.iterdir()):
            if not candidate.is_dir():
                continue
            placement_id = candidate.name
            lookup.setdefault(
                placement_id,
                _PlacementInfo(placement_id=placement_id, template_id=None, expected_variants=None),
            )


def _collect_manifest_lookup(workspace: CampaignWorkspace) -> Dict[str, PlacementManifest]:
    manifests: Dict[str, PlacementManifest] = {}
    for manifest in workspace.iter_manifests() or ():
        manifests[manifest.placement_id] = manifest
    return manifests


def _match_manifest_route(manifest: PlacementManifest, route_id: str) -> Optional[Iterable[int]]:
    for entry in manifest.routes:
        if entry.route_id == route_id:
            return [variant.index for variant in entry.variants]
    return None


def _discover_variant_files(path: Path) -> tuple[Dict[int, Path], List[str]]:
    variants: Dict[int, Path] = {}
    orphans: List[str] = []
    if not path.exists():
        return variants, orphans
    for candidate in path.iterdir():
        if not candidate.is_file():
            continue
        match = _VARIANT_PATTERN.match(candidate.name)
        if match:
            index = int(match.group("index")) - 1
            variants[index] = candidate
        else:
            orphans.append(candidate.name)
    return variants, orphans


def build_campaign_status(workspace: CampaignWorkspace) -> CampaignStatusReport:
    """Compute the current generation status for the given campaign."""

    config = workspace.load_config()
    routes = list(workspace.iter_routes() or [])
    placement_lookup = _build_placement_lookup(config)
    _include_ondisk_placements(placement_lookup, workspace, routes)
    manifests = _collect_manifest_lookup(workspace)

    for placement_id, manifest in manifests.items():
        if placement_id not in placement_lookup:
            placement_lookup[placement_id] = _PlacementInfo(
                placement_id=placement_id,
                template_id=manifest.template_id,
                expected_variants=None,
            )

    placement_accumulators: Dict[str, _PlacementAccumulator] = {}
    orphan_paths: List[str] = []
    pending_variants: List[PendingVariant] = []
    route_reports: List[RouteStatus] = []

    for route in routes:
        placements_report: List[RoutePlacementStatus] = []
        route_expected_total = 0
        route_generated_total = 0
        route_pending_total = 0

        for placement_id in sorted(placement_lookup):
            placement_info = placement_lookup[placement_id]
            placement_acc = placement_accumulators.setdefault(placement_id, _PlacementAccumulator())
            if placement_info.template_id and not placement_acc.template_id:
                placement_acc.template_id = placement_info.template_id

            placement_dir = workspace.images_dir / route.route_id / placement_id
            variant_files, orphans = _discover_variant_files(placement_dir)
            if orphans:
                orphan_paths.extend(
                    str((placement_dir / orphan).relative_to(workspace.root)) for orphan in orphans
                )

            manifest = manifests.get(placement_id)
            manifest_indexes: set[int] = set()
            if manifest is not None:
                placement_acc.manifest_present = True
                placement_acc.manifest_path = str(
                    workspace.placement_manifest_path(placement_id).relative_to(workspace.root)
                )
                match = _match_manifest_route(manifest, route.route_id)
                if match is not None:
                    placement_acc.manifest_routes += 1
                    manifest_indexes = set(match)

            expected_count = placement_info.expected_variants
            if expected_count is not None:
                target_indexes = set(range(expected_count))
            else:
                target_indexes = set(manifest_indexes) or set(variant_files.keys())

            if not target_indexes and not variant_files and not manifest_indexes:
                # No expectation and no data for this route/placement combo.
                continue

            if target_indexes:
                extra_generated = sorted(idx for idx in variant_files if idx not in target_indexes)
            else:
                extra_generated = []
            if target_indexes:
                missing = sorted(idx for idx in target_indexes if idx not in variant_files)
                generated = len(target_indexes) - len(missing)
                manifest_missing = sorted(
                    idx for idx in target_indexes if idx not in manifest_indexes
                )
                expected_variants = len(target_indexes)
            else:
                missing = []
                generated = len(variant_files)
                manifest_missing = []
                expected_variants = len(variant_files)

            next_index = None
            if missing:
                next_index = missing[0]
            elif expected_count is not None:
                next_index = expected_count
            elif variant_files:
                next_index = max(variant_files) + 1

            placements_report.append(
                RoutePlacementStatus(
                    placement_id=placement_id,
                    expected_variants=expected_variants,
                    generated_variants=generated,
                    pending_variants=missing,
                    extra_generated=extra_generated,
                    manifest_recorded=len(manifest_indexes.intersection(target_indexes)),
                    manifest_missing=manifest_missing,
                    next_variant_index=next_index,
                )
            )

            route_expected_total += expected_variants
            route_generated_total += generated
            route_pending_total += len(missing)

            for idx in missing:
                pending_variants.append(
                    PendingVariant(route_id=route.route_id, placement_id=placement_id, variant_index=idx)
                )

            placement_acc.expected_total += expected_variants
            placement_acc.generated_total += generated
            placement_acc.pending_total += len(missing)
            placement_acc.extra_total += len(extra_generated)
            if generated or extra_generated:
                placement_acc.routes_with_output.add(route.route_id)
            if missing:
                placement_acc.routes_missing.add(route.route_id)

        route_reports.append(
            RouteStatus(
                route_id=route.route_id,
                placements=placements_report,
                total_expected=route_expected_total,
                total_generated=route_generated_total,
                total_pending=route_pending_total,
            )
        )

    placements_report: List[PlacementStatus] = []
    missing_manifests: List[str] = []

    for placement_id in sorted(placement_lookup):
        acc = placement_accumulators.setdefault(placement_id, _PlacementAccumulator())
        manifest_path = workspace.placement_manifest_path(placement_id)
        manifest_present = manifest_path.exists()
        manifest_path_rel = str(manifest_path.relative_to(workspace.root))
        if manifest_present:
            acc.manifest_present = True
            acc.manifest_path = manifest_path_rel
        elif acc.generated_total:
            missing_manifests.append(manifest_path_rel)

        placements_report.append(
            PlacementStatus(
                placement_id=placement_id,
                template_id=acc.template_id,
                expected_variants=acc.expected_total,
                generated_variants=acc.generated_total,
                pending_variants=acc.pending_total,
                extra_generated=acc.extra_total,
                routes_with_output=len(acc.routes_with_output),
                routes_missing=sorted(acc.routes_missing),
                manifest_present=acc.manifest_present or manifest_present,
                manifest_path=acc.manifest_path if (acc.manifest_present or manifest_present) else manifest_path_rel,
                manifest_routes=acc.manifest_routes,
            )
        )

    totals = CampaignTotals(
        routes=len(routes),
        placements=len(placement_lookup),
        expected_variants=sum(report.total_expected for report in route_reports),
        generated_variants=sum(report.total_generated for report in route_reports),
        pending_variants=sum(report.total_pending for report in route_reports),
        extra_generated=sum(acc.extra_total for acc in placement_accumulators.values()),
    )

    return CampaignStatusReport(
        campaign_id=config.campaign_id,
        totals=totals,
        routes=route_reports,
        placements=placements_report,
        pending=pending_variants,
        orphan_files=orphan_paths,
        missing_manifests=missing_manifests,
    )


class CampaignStatusPayload(BaseModel):
    """Input payload for campaign status tools."""

    model_config = ConfigDict(populate_by_name=True)

    campaign_id: str = Field(alias="campaignId")
    project_root: Optional[str] = Field(default=None, alias="projectRoot")


def normalize_campaign_status_payload(
    payload: CampaignStatusPayload | dict[str, object] | str,
) -> CampaignStatusPayload:
    """Normalize an arbitrary payload into a structured CampaignStatusPayload."""

    if isinstance(payload, CampaignStatusPayload):
        return payload
    if isinstance(payload, str):
        data: dict[str, object] = {"campaign_id": payload}
    elif isinstance(payload, dict):
        data = payload
    else:
        raise TypeError(f"Unsupported campaign status payload type: {type(payload)!r}")
    return CampaignStatusPayload.model_validate(data)
