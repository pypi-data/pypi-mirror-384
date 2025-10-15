from __future__ import annotations

from datetime import datetime
from math import gcd
from pathlib import Path

import pytest
from PIL import Image

from imagemcp.campaign import CampaignWorkspace
from imagemcp.campaign.runner import (
    DeterministicProviderError,
    enforce_deterministic_provider,
    execute_generation,
    plan_from_batch_spec,
    plan_generation,
)
from imagemcp.campaign.schemas import (
    BatchPlacement,
    BatchRoute,
    CampaignBrief,
    CampaignConfig,
    CampaignRoute,
    DeterministicBatchSpec,
    PlacementRef,
    RouteSource,
)
from imagemcp.storage import ProjectPaths


def _create_working_workspace(tmp_path: Path, placement_template: str = "meta_feed_square") -> CampaignWorkspace:
    project_root = tmp_path / "project"
    project_root.mkdir()
    paths = ProjectPaths.create(project_root, Path("artifacts"))
    paths.ensure_directories()
    workspace = CampaignWorkspace(paths, "test_campaign")
    workspace.ensure_scaffold()

    config = CampaignConfig(
        campaign_id="test_campaign",
        name="Test Campaign",
        brief=CampaignBrief(objective="Boost sales"),
        placements=[PlacementRef(template_id=placement_template)],
    )
    workspace.save_config(config)

    route = CampaignRoute(
        route_id="primary_route",
        name="Primary Route",
        source=RouteSource.MANUAL,
        summary="Primary route summary",
        prompt_template="Render the hero image",
    )
    workspace.save_route(route)
    return workspace


def test_enforce_deterministic_provider_accepts_aliases() -> None:
    enforce_deterministic_provider("openrouter")
    enforce_deterministic_provider("openrouter:gemini-2.5-flash-image-preview")
    enforce_deterministic_provider("mock")


def test_enforce_deterministic_provider_rejects_unknown() -> None:
    with pytest.raises(DeterministicProviderError) as exc:
        enforce_deterministic_provider("anthropic:claude")
    assert "Allowed providers" in str(exc.value)


def test_plan_generation_infers_template_geometry_and_persists_config(tmp_path: Path) -> None:
    workspace = _create_working_workspace(tmp_path)
    config = workspace.load_config()

    plans = plan_generation(
        workspace,
        config,
        routes=None,
        placements=None,
        variants_override=1,
        provider_override=None,
    )

    assert plans, "expected at least one variant plan"
    plan = plans[0]
    assert plan.size == "1080x1080"
    assert plan.aspect_ratio == "1:1"

    updated_config = workspace.load_config()
    placement = updated_config.placements[0]
    assert placement.width == 1080
    assert placement.height == 1080
    assert placement.aspect_ratio == "1:1"


def test_execute_generation_uses_requested_size(tmp_path: Path) -> None:
    workspace = _create_working_workspace(tmp_path, placement_template="meta_story_vertical")
    config = workspace.load_config()

    plans = plan_generation(
        workspace,
        config,
        routes=None,
        placements=None,
        variants_override=1,
        provider_override=None,
    )
    plan = plans[0]

    stats = execute_generation(workspace, [plan], generator_kind="mock")
    assert stats.generated == 1

    with Image.open(plan.output_path) as img:
        assert img.size == (1080, 1920)

    manifest = workspace.load_manifest(plan.placement_id)
    route_entry = next(iter(manifest.routes), None)
    assert route_entry is not None
    variant = next(iter(route_entry.variants), None)
    assert variant is not None
    assert variant.params.get("size") == plan.size
    assert variant.params.get("aspect_ratio") == plan.aspect_ratio


def test_plan_from_batch_spec_respects_dimension_overrides(tmp_path: Path) -> None:
    workspace = _create_working_workspace(tmp_path)

    spec = DeterministicBatchSpec(
        campaign_id="test_campaign",
        run_id="test_run",
        created_at=datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        routes=[
            BatchRoute(
                route_id="primary_route",
                prompt="Render the hero image",
            )
        ],
        placements=[
            BatchPlacement(
                placement_id="meta_feed_square",
                template_id="meta_feed_square",
                dimensions={"width": 1200, "height": 628},
            )
        ],
        variants_per_placement=1,
    )

    plans = plan_from_batch_spec(workspace, spec)
    assert len(plans) == 1
    plan = plans[0]
    assert plan.size == "1200x628"
    expected_ratio = f"{1200 // gcd(1200, 628)}:{628 // gcd(1200, 628)}"
    assert plan.aspect_ratio == expected_ratio
    assert plan.placement.width == 1200
    assert plan.placement.height == 628
