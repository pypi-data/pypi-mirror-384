from __future__ import annotations

import math
from typing import Iterable, List, Optional

import shutil

from ..templates_catalog import get_placement_template
from .workspace import CampaignWorkspace
from .schemas import CampaignRoute, PlacementRef


def _reduced_ratio(width: Optional[int], height: Optional[int]) -> Optional[str]:
    if not width or not height:
        return None
    if width <= 0 or height <= 0:
        return None
    gcd = math.gcd(width, height)
    if gcd <= 0:
        return None
    return f"{width // gcd}:{height // gcd}"


def enrich_placement_geometry(placement: PlacementRef) -> PlacementRef:
    """Populate placement width/height/aspect from the template catalog when missing."""

    template = get_placement_template(placement.template_id)
    if not template:
        return placement

    dims = template.get("dimensions") or {}
    template_width = dims.get("width")
    template_height = dims.get("height")
    template_aspect = template.get("aspect_ratio")

    updates: dict[str, object] = {}
    if placement.width is None and isinstance(template_width, int):
        updates["width"] = template_width
    if placement.height is None and isinstance(template_height, int):
        updates["height"] = template_height

    aspect_candidate: Optional[str] = placement.aspect_ratio
    if not aspect_candidate and isinstance(template_aspect, str) and template_aspect.strip():
        aspect_candidate = template_aspect.strip()

    raw_width = updates.get("width", placement.width)
    raw_height = updates.get("height", placement.height)
    target_width = raw_width if isinstance(raw_width, int) and raw_width > 0 else None
    target_height = raw_height if isinstance(raw_height, int) and raw_height > 0 else None
    if not aspect_candidate:
        aspect_candidate = _reduced_ratio(target_width, target_height)

    if aspect_candidate and placement.aspect_ratio is None:
        updates["aspect_ratio"] = aspect_candidate

    if not updates:
        return placement
    return placement.model_copy(update=updates)


def add_route_from_args(
    workspace: CampaignWorkspace,
    route_id: str,
    *,
    name: Optional[str] = None,
    summary: Optional[str] = None,
    prompt_template: Optional[str] = None,
    source: Optional[str] = None,
    prompt_tokens: Optional[Iterable[str]] = None,
    copy_tokens: Optional[Iterable[str]] = None,
    notes: Optional[str] = None,
) -> CampaignRoute:
    route = CampaignRoute(
        route_id=route_id,
        name=name or route_id.replace("_", " ").title(),
        summary=summary or "TODO: fill summary",
        prompt_template=prompt_template or "TODO: fill prompt",
        source=source or "manual",
        prompt_tokens=list(prompt_tokens or ()),
        copy_tokens=list(copy_tokens or ()),
        notes=notes,
    )
    workspace.save_route(route)
    return route


def add_placement_to_campaign(
    workspace: CampaignWorkspace,
    placement_id: str,
    *,
    template_id: Optional[str] = None,
    variants: Optional[int] = None,
    copy_tokens: Optional[Iterable[str]] = None,
    provider: Optional[str] = None,
    notes: Optional[str] = None,
) -> PlacementRef:
    config = workspace.load_config()
    template_slug = template_id or placement_id
    placement_ref = PlacementRef(
        template_id=template_slug,
        override_id=placement_id if placement_id != template_slug else None,
        variants=variants,
        copy_tokens=list(copy_tokens or ()),
        provider=provider,
        notes=notes,
    )
    placement_ref = enrich_placement_geometry(placement_ref)
    placements = [ref for ref in config.placements if ref.effective_id != placement_id]
    placements.append(placement_ref)
    config = config.model_copy(update={"placements": placements})
    workspace.save_config(config)
    return placement_ref


def ensure_campaign_exists(workspace: CampaignWorkspace) -> None:
    if not workspace.config_path.exists():
        raise FileNotFoundError(
            f"Campaign '{workspace.campaign_id}' is not initialized."
        )


def list_routes(workspace: CampaignWorkspace) -> List[CampaignRoute]:
    return list(workspace.iter_routes() or [])


def load_route(workspace: CampaignWorkspace, route_id: str) -> CampaignRoute:
    return workspace.load_route(route_id)


def remove_route(
    workspace: CampaignWorkspace,
    route_id: str,
    *,
    delete_assets: bool = False,
) -> Path:
    path = workspace.route_path(route_id)
    if not path.exists():
        raise FileNotFoundError(f"Route '{route_id}' not found")
    route_dir = path.parent
    if delete_assets and route_dir.exists():
        shutil.rmtree(route_dir)
        return route_dir
    path.unlink()
    # clean up parent directory if empty
    try:
        if not any(route_dir.iterdir()):
            route_dir.rmdir()
    except OSError:
        pass
    return path


def list_placements(workspace: CampaignWorkspace) -> List[PlacementRef]:
    config = workspace.load_config()
    return list(config.placements or [])


def get_placement(workspace: CampaignWorkspace, placement_id: str) -> PlacementRef:
    for placement in list_placements(workspace):
        if placement.effective_id == placement_id:
            return placement
    raise FileNotFoundError(f"Placement '{placement_id}' not found in campaign.yaml")


def remove_placement_from_campaign(
    workspace: CampaignWorkspace,
    placement_id: str,
) -> None:
    config = workspace.load_config()
    filtered = [ref for ref in config.placements if ref.effective_id != placement_id]
    if len(filtered) == len(config.placements):
        raise FileNotFoundError(f"Placement '{placement_id}' not found in campaign.yaml")
    config = config.model_copy(update={"placements": filtered})
    workspace.save_config(config)


__all__ = [
    "add_route_from_args",
    "add_placement_to_campaign",
    "enrich_placement_geometry",
    "ensure_campaign_exists",
    "list_routes",
    "load_route",
    "remove_route",
    "list_placements",
    "get_placement",
    "remove_placement_from_campaign",
]
