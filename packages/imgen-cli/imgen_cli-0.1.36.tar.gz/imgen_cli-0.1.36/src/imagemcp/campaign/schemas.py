from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

ISO_8601 = "%Y-%m-%dT%H:%M:%SZ"
CAMPAIGN_SCHEMA_VERSION = "0.1"
PLACEMENT_MANIFEST_VERSION = "0.1"
BATCH_SPEC_VERSION = "0.1"
EXPORT_MANIFEST_VERSION = "0.1"


class CampaignMode(str, Enum):
    CAMPAIGN = "campaign"
    HYBRID = "hybrid"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"


class RouteSource(str, Enum):
    AI = "ai"
    MANUAL = "manual"
    CATALOG = "catalog"


class ReviewState(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REVISE = "revise"


class CampaignBrief(BaseModel):
    objective: str
    offer: Optional[str] = None
    audience: List[str] = Field(default_factory=list)
    tone: str = "balanced"
    key_messages: List[str] = Field(default_factory=list)
    brand_constraints: List[str] = Field(default_factory=list)
    deadline: Optional[str] = None
    references: List[str] = Field(default_factory=list)


class PlacementRef(BaseModel):
    template_id: str
    override_id: Optional[str] = None
    variants: Optional[int] = None
    copy_tokens: List[str] = Field(default_factory=list)
    provider: Optional[str] = None
    notes: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None

    @property
    def effective_id(self) -> str:
        return self.override_id or self.template_id


class VariantDefaults(BaseModel):
    count: int = 3
    provider_params: Dict[str, object] = Field(default_factory=dict)
    file_format: str = "png"
    resolution_behavior: Literal["fit", "fill", "stretch"] = "fit"


class RouteSeed(BaseModel):
    route_id: str
    name: str
    summary: str
    prompt_tokens: List[str] = Field(default_factory=list)
    copy_tokens: List[str] = Field(default_factory=list)
    status: ReviewState = ReviewState.PENDING


class CampaignConfig(BaseModel):
    version: str = Field(default=CAMPAIGN_SCHEMA_VERSION)
    campaign_id: str
    name: str
    mode: CampaignMode = CampaignMode.CAMPAIGN
    status: CampaignStatus = CampaignStatus.DRAFT
    tags: List[str] = Field(default_factory=list)
    brief: CampaignBrief
    placements: List[PlacementRef]
    routes: List[RouteSeed] = Field(default_factory=list)
    default_provider: str = "openrouter:gemini-2.5-flash-image-preview"
    variant_defaults: VariantDefaults = Field(default_factory=VariantDefaults)
    assets: Dict[str, str] = Field(default_factory=dict)
    notes: Optional[str] = None

    @field_validator("campaign_id")
    @classmethod
    def validate_campaign_id(cls, value: str) -> str:
        if value.lower() != value:
            raise ValueError("campaign_id must be lowercase")
        if not value:
            raise ValueError("campaign_id cannot be empty")
        return value


class CampaignRoute(BaseModel):
    version: str = Field(default=CAMPAIGN_SCHEMA_VERSION)
    route_id: str
    name: str
    source: RouteSource
    summary: str
    prompt_template: str
    prompt_tokens: List[str] = Field(default_factory=list)
    copy_tokens: List[str] = Field(default_factory=list)
    asset_refs: List[str] = Field(default_factory=list)
    status: ReviewState = ReviewState.PENDING
    notes: Optional[str] = None


class ManifestVariant(BaseModel):
    variant_id: str
    index: int
    file: str
    thumbnail: str
    provider: str
    prompt: str
    negative_prompt: Optional[str] = None
    seed: int
    params: Dict[str, object] = Field(default_factory=dict)
    review_state: ReviewState = ReviewState.PENDING
    review_notes: Optional[str] = None
    artifacts: List[str] = Field(default_factory=list)
    created_at: str

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: str) -> str:
        datetime.strptime(value, ISO_8601)
        return value


class ManifestRouteEntry(BaseModel):
    route_id: str
    summary: str
    status: ReviewState = ReviewState.PENDING
    variants: List[ManifestVariant]


class PlacementManifest(BaseModel):
    version: str = Field(default=PLACEMENT_MANIFEST_VERSION)
    campaign_id: str
    placement_id: str
    template_id: str
    routes: List[ManifestRouteEntry]
    updated_at: str
    notes: Optional[str] = None

    @field_validator("updated_at")
    @classmethod
    def validate_updated_at(cls, value: str) -> str:
        datetime.strptime(value, ISO_8601)
        return value


class BatchRoute(BaseModel):
    route_id: str
    prompt: str
    copy_tokens: List[str] = Field(default_factory=list)
    seed_base: Optional[int] = None


class BatchPlacement(BaseModel):
    placement_id: str
    template_id: str
    dimensions: Optional[Dict[str, int]] = None
    provider: Optional[str] = None
    variants: Optional[int] = None


class ResumeMarker(BaseModel):
    route_id: Optional[str] = None
    placement_id: Optional[str] = None
    variant_index: Optional[int] = None


class DeterministicBatchSpec(BaseModel):
    version: str = Field(default=BATCH_SPEC_VERSION)
    campaign_id: str
    run_id: str
    created_at: str
    author: Optional[str] = None
    routes: List[BatchRoute]
    placements: List[BatchPlacement]
    variants_per_placement: int = 3
    provider: Optional[str] = None
    provider_params: Dict[str, object] = Field(default_factory=dict)
    seed_strategy: Literal["increment", "fixed", "random"] = "increment"
    output_root: str = "images/"
    resume_from: Optional[ResumeMarker] = None

    @field_validator("created_at")
    @classmethod
    def validate_created_at(cls, value: str) -> str:
        datetime.strptime(value, ISO_8601)
        return value


class ExportRoute(BaseModel):
    route_id: str
    summary: str


class ExportFile(BaseModel):
    path: str
    placement_id: str
    variant_id: str
    review_state: ReviewState
    checksum: str


class ExportCsv(BaseModel):
    name: str
    path: str
    profile: str
    checksum: str
    row_count: int


class ExportManifest(BaseModel):
    version: str = Field(default=EXPORT_MANIFEST_VERSION)
    campaign_id: str
    platform: str
    export_id: str
    generated_at: str
    routes: List[ExportRoute]
    placements: List[str]
    creator: Optional[str] = None
    include_states: List[ReviewState] = Field(default_factory=lambda: [ReviewState.APPROVED])
    files: List[ExportFile]
    csv_files: List[ExportCsv] = Field(default_factory=list)
    notes: Optional[str] = None

    @field_validator("generated_at")
    @classmethod
    def validate_generated_at(cls, value: str) -> str:
        datetime.strptime(value, ISO_8601)
        return value


def load_yaml(path: Path) -> dict:
    import yaml

    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def dump_yaml(path: Path, data: dict) -> None:
    import yaml

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        yaml.safe_dump(data, fh, sort_keys=False)


def load_json(path: Path) -> dict:
    import json

    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def dump_json(path: Path, data: dict) -> None:
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")
