from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from ..storage import ProjectPaths
from .schemas import (
    CAMPAIGN_SCHEMA_VERSION,
    BATCH_SPEC_VERSION,
    EXPORT_MANIFEST_VERSION,
    PLACEMENT_MANIFEST_VERSION,
    CampaignBrief,
    CampaignConfig,
    CampaignRoute,
    DeterministicBatchSpec,
    ExportManifest,
    PlacementManifest,
    dump_json,
    dump_yaml,
    load_json,
    load_yaml,
)


def _iso_now() -> str:
    return datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(slots=True)
class CampaignWorkspace:
    """Represents a single campaign workspace within a project."""

    paths: ProjectPaths
    campaign_id: str

    @property
    def root(self) -> Path:
        return self.paths.campaign_dir(self.campaign_id)

    @property
    def config_path(self) -> Path:
        return self.root / "campaign.yaml"

    @property
    def routes_dir(self) -> Path:
        return self.paths.campaign_routes_dir(self.campaign_id)

    @property
    def placements_dir(self) -> Path:
        return self.paths.campaign_placements_dir(self.campaign_id)

    @property
    def thumbnails_dir(self) -> Path:
        return self.paths.campaign_thumbnails_dir(self.campaign_id)

    @property
    def images_dir(self) -> Path:
        return self.root / "images"

    @property
    def exports_dir(self) -> Path:
        return self.paths.campaign_exports_dir(self.campaign_id)

    @property
    def logs_dir(self) -> Path:
        return self.paths.campaign_logs_dir(self.campaign_id)

    def ensure_scaffold(self) -> None:
        self.routes_dir.mkdir(parents=True, exist_ok=True)
        self.placements_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnails_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Campaign config helpers
    # ------------------------------------------------------------------
    def load_config(self) -> CampaignConfig:
        raw = load_yaml(self.config_path)
        if not raw:
            raise FileNotFoundError(f"Campaign config missing at {self.config_path}")
        return CampaignConfig.model_validate(raw)

    def save_config(self, config: CampaignConfig) -> None:
        payload = config.model_dump(mode="json", exclude_none=True)
        dump_yaml(self.config_path, payload)

    # ------------------------------------------------------------------
    # Route helpers
    # ------------------------------------------------------------------
    def route_path(self, route_id: str) -> Path:
        return self.routes_dir / route_id / "route.yaml"

    def load_route(self, route_id: str) -> CampaignRoute:
        path = self.route_path(route_id)
        raw = load_yaml(path)
        return CampaignRoute.model_validate(raw)

    def save_route(self, route: CampaignRoute) -> None:
        payload = route.model_dump(mode="json", exclude_none=True)
        dump_yaml(self.route_path(route.route_id), payload)

    def iter_routes(self) -> Iterator[CampaignRoute]:
        if not self.routes_dir.exists():
            return
        for candidate in sorted(self.routes_dir.glob("*/route.yaml")):
            raw = load_yaml(candidate)
            yield CampaignRoute.model_validate(raw)

    # ------------------------------------------------------------------
    # Placement manifest helpers
    # ------------------------------------------------------------------
    def placement_manifest_path(self, placement_id: str) -> Path:
        return self.placements_dir / placement_id / "manifest.json"

    def load_manifest(self, placement_id: str) -> PlacementManifest:
        path = self.placement_manifest_path(placement_id)
        raw = load_json(path)
        return PlacementManifest.model_validate(raw)

    def save_manifest(self, manifest: PlacementManifest) -> None:
        payload = manifest.model_dump(mode="json", exclude_none=True)
        dump_json(self.placement_manifest_path(manifest.placement_id), payload)

    def iter_manifests(self) -> Iterator[PlacementManifest]:
        if not self.placements_dir.exists():
            return
        for candidate in sorted(self.placements_dir.glob("*/manifest.json")):
            raw = load_json(candidate)
            yield PlacementManifest.model_validate(raw)

    # ------------------------------------------------------------------
    # Batch specs
    # ------------------------------------------------------------------
    def batch_spec_path(self, name: str = "batch.yaml") -> Path:
        return self.root / name

    def load_batch_spec(self, path: Optional[Path] = None) -> DeterministicBatchSpec:
        resolved = path or self.batch_spec_path()
        raw = load_yaml(resolved)
        return DeterministicBatchSpec.model_validate(raw)

    def save_batch_spec(self, spec: DeterministicBatchSpec, path: Optional[Path] = None) -> Path:
        payload = spec.model_dump(mode="json", exclude_none=True)
        destination = path or self.batch_spec_path()
        dump_yaml(destination, payload)
        return destination

    # ------------------------------------------------------------------
    # Export manifests
    # ------------------------------------------------------------------
    def export_manifest_path(self, platform: str, export_id: Optional[str] = None) -> Path:
        timestamp = export_id or _iso_now().replace(":", "")
        return self.exports_dir / platform / timestamp / "manifest.json"

    def load_export_manifest(self, path: Path) -> ExportManifest:
        raw = load_json(path)
        return ExportManifest.model_validate(raw)

    def save_export_manifest(self, manifest: ExportManifest, path: Optional[Path] = None) -> Path:
        payload = manifest.model_dump(mode="json", exclude_none=True)
        destination = path or self.export_manifest_path(manifest.platform, manifest.export_id)
        dump_json(destination, payload)
        return destination

    # ------------------------------------------------------------------
    def ensure_default_config(self, name: str, brief: Optional["CampaignBriefPayload"] = None) -> CampaignConfig:
        """Create a default campaign config if missing and return it."""
        if self.config_path.exists():
            return self.load_config()
        self.ensure_scaffold()
        data = brief or {"objective": "TODO: fill campaign objective"}
        base_brief = CampaignBrief.model_validate(data)
        config = CampaignConfig(
            campaign_id=self.campaign_id,
            name=name,
            brief=base_brief,
            placements=[],
        )
        self.save_config(config)
        return config


CampaignBriefPayload = dict[str, object]
