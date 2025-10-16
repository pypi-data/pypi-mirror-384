from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

import shutil

from PIL import Image

from ..defaults import DEFAULT_GENERATOR
from ..generator import GenerationResult, ProviderExecutionError, build_generator
from .schemas import (
    CampaignConfig,
    CampaignRoute,
    ManifestRouteEntry,
    ManifestVariant,
    PlacementManifest,
    PlacementRef,
    ReviewState,
    RouteSource,
    DeterministicBatchSpec,
)
from .workspace import CampaignWorkspace
from .setup import enrich_placement_geometry

SUPPORTED_DETERMINISTIC_PROVIDERS = {
    "openrouter",
    "mock",
}


class DeterministicProviderError(RuntimeError):
    """Raised when a provider without deterministic seeding is requested."""


@dataclass(slots=True)
class VariantPlan:
    route: CampaignRoute
    placement: PlacementRef
    placement_id: str
    variant_index: int
    prompt: str
    provider: str
    seed: int
    output_path: Path
    thumbnail_path: Path
    manifest_file: Path
    size: Optional[str] = None
    aspect_ratio: Optional[str] = None
    provider_params: Dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class GenerationStats:
    campaign_id: str
    generated: int = 0
    warnings: List[str] = field(default_factory=list)
    events: List[Dict[str, object]] = field(default_factory=list)

    def extend(self, warnings: Iterable[str]) -> None:
        for warning in warnings:
            if warning not in self.warnings:
                self.warnings.append(warning)


def _coerce_positive_int(value: object) -> Optional[int]:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    try:
        candidate = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return candidate if candidate > 0 else None


def _reduced_ratio(width: Optional[int], height: Optional[int]) -> Optional[str]:
    if not width or not height:
        return None
    if width <= 0 or height <= 0:
        return None
    gcd = math.gcd(width, height)
    if gcd <= 0:
        return None
    numerator = width // gcd
    denominator = height // gcd
    if numerator <= 0 or denominator <= 0:
        return None
    return f"{numerator}:{denominator}"


def _resolve_plan_geometry(
    placement: PlacementRef,
    override_dimensions: Optional[Dict[str, object]] = None,
) -> tuple[Optional[str], Optional[str]]:
    override_width = None
    override_height = None
    if override_dimensions:
        override_width = _coerce_positive_int(override_dimensions.get("width"))
        override_height = _coerce_positive_int(override_dimensions.get("height"))

    width = override_width or _coerce_positive_int(placement.width)
    height = override_height or _coerce_positive_int(placement.height)

    aspect_ratio = placement.aspect_ratio.strip() if isinstance(placement.aspect_ratio, str) else None
    if not aspect_ratio and override_dimensions:
        aspect_candidate = override_dimensions.get("aspect_ratio")
        if isinstance(aspect_candidate, str) and aspect_candidate.strip():
            aspect_ratio = aspect_candidate.strip()

    size = None
    if width and height:
        size = f"{width}x{height}"
        if not aspect_ratio:
            aspect_ratio = _reduced_ratio(width, height)

    return size, aspect_ratio


def _apply_dimensions_override(
    placement: PlacementRef,
    override: Optional[Dict[str, object]],
) -> PlacementRef:
    if not override:
        return placement

    width = _coerce_positive_int(override.get("width"))
    height = _coerce_positive_int(override.get("height"))
    updates: Dict[str, object] = {}
    if width is not None:
        updates["width"] = width
    if height is not None:
        updates["height"] = height

    aspect_candidate = override.get("aspect_ratio")
    if isinstance(aspect_candidate, str) and aspect_candidate.strip():
        updates["aspect_ratio"] = aspect_candidate.strip()
    elif width is not None and height is not None:
        ratio = _reduced_ratio(width, height)
        if ratio:
            updates["aspect_ratio"] = ratio

    if not updates:
        return placement
    return placement.model_copy(update=updates)


def _ensure_config_geometry(
    workspace: CampaignWorkspace,
    config: CampaignConfig,
) -> CampaignConfig:
    placements: List[PlacementRef] = []
    updated = False
    for ref in config.placements:
        enriched = enrich_placement_geometry(ref)
        placements.append(enriched)
        if (
            enriched.width != ref.width
            or enriched.height != ref.height
            or enriched.aspect_ratio != ref.aspect_ratio
        ):
            updated = True

    if updated:
        config = config.model_copy(update={"placements": placements})
        workspace.save_config(config)
        return config
    return config


def enforce_deterministic_provider(provider: str) -> None:
    normalized = (provider or "").lower()
    allowed = {item.lower() for item in SUPPORTED_DETERMINISTIC_PROVIDERS}
    for candidate in allowed:
        if normalized == candidate or normalized.startswith(f"{candidate}:"):
            return
    allowed_display = ", ".join(sorted(SUPPORTED_DETERMINISTIC_PROVIDERS))
    raise DeterministicProviderError(
        "Provider '{provider}' is not certified for deterministic seeding. "
        "Allowed providers: {allowed}.".format(
            provider=provider,
            allowed=allowed_display,
        )
    )


def compute_variant_seed(
    campaign_id: str,
    route_id: str,
    placement_id: str,
    variant_index: int,
    seed_base: Optional[int] = None,
) -> int:
    """Derive a stable seed from campaign metadata."""
    base = seed_base or 0
    payload = f"{campaign_id}:{route_id}:{placement_id}:{variant_index}:{base}".encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:8], 16)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_thumbnail(source: Path, destination: Path, size: int = 320) -> None:
    ensure_parent(destination)
    with Image.open(source) as img:
        img.thumbnail((size, size))
        img.save(destination)


def build_prompt(route: CampaignRoute, placement: PlacementRef) -> str:
    tokens = list(route.prompt_tokens)
    tokens.extend(placement.copy_tokens)
    prompt = route.prompt_template.strip()
    if tokens:
        prompt = f"{prompt}\n\n" + "\n".join(tokens)
    return prompt


def plan_generation(
    workspace: CampaignWorkspace,
    config: CampaignConfig,
    routes: Sequence[str] | None,
    placements: Sequence[str] | None,
    variants_override: Optional[int],
    provider_override: Optional[str],
) -> List[VariantPlan]:
    config = _ensure_config_geometry(workspace, config)
    available_routes: Dict[str, CampaignRoute] = {route.route_id: route for route in workspace.iter_routes()}
    selected_routes = routes or list(available_routes)
    plans: List[VariantPlan] = []
    default_provider = provider_override or config.default_provider
    enforce_deterministic_provider(default_provider)

    for route_id in selected_routes:
        route = available_routes.get(route_id)
        if route is None:
            raise RuntimeError(f"Route '{route_id}' not found in campaign workspace")
        for placement in config.placements:
            placement_id = placement.override_id or placement.template_id
            if placements and placement_id not in placements and placement.template_id not in placements:
                continue
            variant_count = variants_override or placement.variants or config.variant_defaults.count
            provider = placement.provider or default_provider
            enforce_deterministic_provider(provider)
            base_provider_params = dict(config.variant_defaults.provider_params)
            size, aspect_ratio = _resolve_plan_geometry(placement)
            for index in range(int(variant_count)):
                seed = compute_variant_seed(config.campaign_id, route.route_id, placement_id, index)
                file_name = f"v{index + 1:03d}.png"
                image_path = workspace.root / "images" / route.route_id / placement_id / file_name
                thumbnail_path = workspace.thumbnails_dir / route.route_id / placement_id / file_name
                manifest_path = workspace.placement_manifest_path(placement_id)
                plan = VariantPlan(
                    route=route,
                    placement=placement,
                    placement_id=placement_id,
                    variant_index=index,
                    prompt=build_prompt(route, placement),
                    provider=provider,
                    seed=seed,
                    output_path=image_path,
                    thumbnail_path=thumbnail_path,
                    manifest_file=manifest_path,
                    size=size,
                    aspect_ratio=aspect_ratio,
                    provider_params=base_provider_params,
                )
                plans.append(plan)
    return plans


def plan_from_batch_spec(
    workspace: CampaignWorkspace,
    spec: DeterministicBatchSpec,
) -> List[VariantPlan]:
    config = workspace.load_config()
    config = _ensure_config_geometry(workspace, config)
    placement_lookup: Dict[str, PlacementRef] = {}
    for placement in config.placements:
        placement_id = placement.override_id or placement.template_id
        placement_lookup[placement_id] = placement

    plans: List[VariantPlan] = []
    for route in spec.routes:
        route_summary = route.prompt.splitlines()[0][:120] if route.prompt else route.route_id
        campaign_route = CampaignRoute(
            route_id=route.route_id,
            name=route.route_id.replace("_", " ").title(),
            source=RouteSource.MANUAL,
            summary=route_summary,
            prompt_template=route.prompt,
            prompt_tokens=route.copy_tokens,
            copy_tokens=route.copy_tokens,
        )
        for placement in spec.placements:
            variants = placement.variants or spec.variants_per_placement
            placement_id = placement.placement_id
            base_seed = route.seed_base or 0
            template_ref = placement_lookup.get(placement_id)
            reference = PlacementRef(
                template_id=placement.template_id,
                override_id=placement.placement_id,
                variants=variants,
                copy_tokens=template_ref.copy_tokens if template_ref else [],
                provider=placement.provider or (template_ref.provider if template_ref else None),
                width=template_ref.width if template_ref else None,
                height=template_ref.height if template_ref else None,
                aspect_ratio=template_ref.aspect_ratio if template_ref else None,
            )
            reference = enrich_placement_geometry(reference)
            reference = _apply_dimensions_override(reference, placement.dimensions)
            provider = reference.provider or spec.provider or config.default_provider
            enforce_deterministic_provider(provider)
            size, aspect_ratio = _resolve_plan_geometry(reference, placement.dimensions)
            for index in range(int(variants)):
                seed = compute_variant_seed(spec.campaign_id, route.route_id, placement_id, base_seed + index)
                file_name = f"v{index + 1:03d}.png"
                image_path = workspace.root / "images" / route.route_id / placement_id / file_name
                thumbnail_path = workspace.thumbnails_dir / route.route_id / placement_id / file_name
                manifest_path = workspace.placement_manifest_path(placement_id)
                plan = VariantPlan(
                    route=campaign_route,
                    placement=reference,
                    placement_id=placement_id,
                    variant_index=index,
                    prompt=route.prompt,
                    provider=provider,
                    seed=seed,
                    output_path=image_path,
                    thumbnail_path=thumbnail_path,
                    manifest_file=manifest_path,
                    size=size,
                    aspect_ratio=aspect_ratio,
                    provider_params=dict(spec.provider_params),
                )
                plans.append(plan)
    return plans


def execute_generation(
    workspace: CampaignWorkspace,
    plans: Sequence[VariantPlan],
    generator_kind: Optional[str],
) -> GenerationStats:
    stats = GenerationStats(campaign_id=workspace.campaign_id)
    if not plans:
        return stats

    temp_dir = workspace.root / ".tmp" / datetime.utcnow().strftime("%Y%m%d%H%M%S")
    selected_generator = generator_kind or DEFAULT_GENERATOR
    generator = build_generator(temp_dir, selected_generator)
    normalized_generator = (selected_generator or "").lower()

    for plan in plans:
        effective_provider = plan.provider or normalized_generator or "openrouter"
        if normalized_generator == "mock":
            effective_provider = "mock"
        plan.provider = effective_provider
        try:
            result = generator.generate(
                plan.prompt,
                1,
                seed=plan.seed,
                provider=effective_provider,
                size=plan.size,
                aspect_ratio=plan.aspect_ratio,
                provider_options=plan.provider_params,
            )
        except ProviderExecutionError as exc:
            exc.attach_context(
                {
                    "campaign_id": workspace.campaign_id,
                    "route_id": plan.route.route_id,
                    "placement_id": plan.placement_id,
                    "variant_index": plan.variant_index,
                    "generator": normalized_generator or selected_generator,
                }
            )
            raise
        except RuntimeError as exc:
            raise ProviderExecutionError(
                provider=effective_provider,
                generator=normalized_generator or selected_generator or "openrouter",
                message=str(exc),
                context={
                    "campaign_id": workspace.campaign_id,
                    "route_id": plan.route.route_id,
                    "placement_id": plan.placement_id,
                    "variant_index": plan.variant_index,
                    "generator": normalized_generator or selected_generator,
                },
            ) from exc

        stats.extend(result.warnings)
        if not result.images:
            raise RuntimeError("Generator returned no images")
        artifact = result.images[0]
        ensure_parent(plan.output_path)
        ensure_parent(plan.thumbnail_path)
        if plan.output_path.exists():
            plan.output_path.unlink()
        artifact.processed_path.rename(plan.output_path)
        write_thumbnail(plan.output_path, plan.thumbnail_path)
        _upsert_manifest(workspace, plan, plan.output_path)
        timestamp = datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        stats.events.append(
            {
                "timestamp": timestamp,
                "campaign_id": workspace.campaign_id,
                "route_id": plan.route.route_id,
                "placement_id": plan.placement_id,
                "variant_index": plan.variant_index,
                "status": "succeeded",
                "provider": effective_provider,
                "prompt": plan.prompt,
                "seed": plan.seed,
                "file": str(plan.output_path.relative_to(workspace.root)),
                "size": plan.size,
                "aspect_ratio": plan.aspect_ratio,
            }
        )
        stats.generated += 1
    shutil.rmtree(temp_dir, ignore_errors=True)
    if hasattr(generator, "close"):
        try:
            generator.close()
        except Exception:  # pragma: no cover - defensive cleanup
            pass
    return stats


def _upsert_manifest(workspace: CampaignWorkspace, plan: VariantPlan, image_path: Path) -> None:
    manifest_path = plan.manifest_file
    if manifest_path.exists():
        manifest = workspace.load_manifest(plan.placement_id)
    else:
        manifest = PlacementManifest(
            campaign_id=workspace.campaign_id,
            placement_id=plan.placement_id,
            template_id=plan.placement.template_id,
            routes=[],
            updated_at=datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        )
    route_entry = None
    for existing in manifest.routes:
        if existing.route_id == plan.route.route_id:
            route_entry = existing
            break
    if route_entry is None:
        route_entry = ManifestRouteEntry(
            route_id=plan.route.route_id,
            summary=plan.route.summary,
            status=plan.route.status,
            variants=[],
        )
        manifest.routes.append(route_entry)

    existing_variant = None
    existing_index = None
    for idx, existing in enumerate(route_entry.variants):
        if existing.index == plan.variant_index:
            existing_variant = existing
            existing_index = idx
            break

    variant_id = f"{plan.route.route_id}-{plan.placement_id}-v{plan.variant_index + 1:03d}"
    params = dict(plan.provider_params or {})
    if plan.size and "size" not in params:
        params["size"] = plan.size
    if plan.aspect_ratio and "aspect_ratio" not in params:
        params["aspect_ratio"] = plan.aspect_ratio
    record = ManifestVariant(
        variant_id=variant_id,
        index=plan.variant_index,
        file=str(image_path.relative_to(workspace.root)),
        thumbnail=str(plan.thumbnail_path.relative_to(workspace.root)),
        provider=plan.provider,
        prompt=plan.prompt,
        seed=plan.seed,
        params=params,
        review_state=ReviewState.PENDING,
        artifacts=[],
        created_at=datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    if existing_variant is not None:
        record.review_state = existing_variant.review_state
        record.review_notes = existing_variant.review_notes
        route_entry.variants[existing_index] = record
    else:
        route_entry.variants.append(record)
        route_entry.variants.sort(key=lambda item: item.index)

    manifest.updated_at = datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    workspace.save_manifest(manifest)
