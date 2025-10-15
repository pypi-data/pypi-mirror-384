from __future__ import annotations

import json
from pathlib import Path

from imagemcp.campaign import build_campaign_status, CampaignWorkspace
from imagemcp.campaign.schemas import (
    CampaignBrief,
    CampaignConfig,
    CampaignRoute,
    ManifestRouteEntry,
    ManifestVariant,
    PlacementManifest,
    PlacementRef,
    ReviewState,
    RouteSource,
)
from imagemcp.cli import main as cli_main
from imagemcp.config import ensure_project_config
from imagemcp.storage import ProjectPaths


def _prepare_sample_campaign(root: Path) -> CampaignWorkspace:
    config = ensure_project_config(root)
    paths = ProjectPaths.create(config.project_root, Path(config.target_root))
    workspace = CampaignWorkspace(paths, "demo_campaign")
    workspace.ensure_scaffold()

    campaign_config = CampaignConfig(
        campaign_id=workspace.campaign_id,
        name="Demo",
        brief=CampaignBrief(objective="Test objective"),
        placements=[
            PlacementRef(template_id="square", variants=3),
            PlacementRef(template_id="vertical", variants=2),
        ],
    )
    workspace.save_config(campaign_config)

    alpha_route = CampaignRoute(
        route_id="alpha",
        name="Alpha",
        source=RouteSource.MANUAL,
        summary="Alpha summary",
        prompt_template="Alpha prompt",
    )
    beta_route = CampaignRoute(
        route_id="beta",
        name="Beta",
        source=RouteSource.MANUAL,
        summary="Beta summary",
        prompt_template="Beta prompt",
    )
    workspace.save_route(alpha_route)
    workspace.save_route(beta_route)

    def _write_variant(route_id: str, placement_id: str, variant_index: int) -> None:
        image_dir = workspace.root / "images" / route_id / placement_id
        image_dir.mkdir(parents=True, exist_ok=True)
        (image_dir / f"v{variant_index:03d}.png").write_bytes(b"demo")

    # alpha/square -> v001, v002
    _write_variant("alpha", "square", 1)
    _write_variant("alpha", "square", 2)
    # beta/square -> v001
    _write_variant("beta", "square", 1)
    # beta/vertical -> v001, v002
    _write_variant("beta", "vertical", 1)
    _write_variant("beta", "vertical", 2)

    timestamp = "2024-01-01T00:00:00Z"
    square_manifest = PlacementManifest(
        campaign_id=workspace.campaign_id,
        placement_id="square",
        template_id="square",
        routes=[
            ManifestRouteEntry(
                route_id="alpha",
                summary="Alpha summary",
                variants=[
                    ManifestVariant(
                        variant_id="alpha-square-v001",
                        index=0,
                        file="images/alpha/square/v001.png",
                        thumbnail="thumbnails/alpha/square/v001.png",
                        provider="mock",
                        prompt="Alpha prompt",
                        seed=111,
                        params={},
                        review_state=ReviewState.PENDING,
                        artifacts=[],
                        created_at=timestamp,
                    ),
                    ManifestVariant(
                        variant_id="alpha-square-v002",
                        index=1,
                        file="images/alpha/square/v002.png",
                        thumbnail="thumbnails/alpha/square/v002.png",
                        provider="mock",
                        prompt="Alpha prompt",
                        seed=112,
                        params={},
                        review_state=ReviewState.PENDING,
                        artifacts=[],
                        created_at=timestamp,
                    ),
                ],
            ),
            ManifestRouteEntry(
                route_id="beta",
                summary="Beta summary",
                variants=[
                    ManifestVariant(
                        variant_id="beta-square-v001",
                        index=0,
                        file="images/beta/square/v001.png",
                        thumbnail="thumbnails/beta/square/v001.png",
                        provider="mock",
                        prompt="Beta prompt",
                        seed=210,
                        params={},
                        review_state=ReviewState.PENDING,
                        artifacts=[],
                        created_at=timestamp,
                    ),
                ],
            ),
        ],
        updated_at=timestamp,
    )
    workspace.save_manifest(square_manifest)

    return workspace


def test_build_campaign_status_partial_generation(tmp_path):
    workspace = _prepare_sample_campaign(tmp_path)

    report = build_campaign_status(workspace)

    assert report.totals.expected_variants == 10
    assert report.totals.generated_variants == 5
    assert report.totals.pending_variants == 5

    square_status = next(item for item in report.placements if item.placement_id == "square")
    assert square_status.manifest_present
    assert square_status.generated_variants == 3
    assert square_status.pending_variants == 3

    vertical_status = next(item for item in report.placements if item.placement_id == "vertical")
    assert vertical_status.generated_variants == 2
    assert vertical_status.pending_variants == 2

    alpha_route = next(item for item in report.routes if item.route_id == "alpha")
    square_entry = next(item for item in alpha_route.placements if item.placement_id == "square")
    assert square_entry.pending_variants == [2]
    vertical_entry = next(item for item in alpha_route.placements if item.placement_id == "vertical")
    assert vertical_entry.pending_variants == [0, 1]

    beta_route = next(item for item in report.routes if item.route_id == "beta")
    beta_square = next(item for item in beta_route.placements if item.placement_id == "square")
    assert beta_square.pending_variants == [1, 2]

    missing_manifest_path = str(
        workspace.placement_manifest_path("vertical").relative_to(workspace.root)
    )
    assert missing_manifest_path in report.missing_manifests
    assert not report.orphan_files


def test_cli_campaign_status_json_output(tmp_path, capsys):
    workspace = _prepare_sample_campaign(tmp_path)
    project_root = workspace.paths.project_root

    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "campaign",
            "status",
            workspace.campaign_id,
            "--json",
        ]
    )
    assert exit_code == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["campaign_id"] == workspace.campaign_id
    assert payload["totals"]["generated_variants"] == 5
    assert payload["totals"]["pending_variants"] == 5

    placements = {item["placement_id"]: item for item in payload["placements"]}
    assert placements["square"]["manifest_present"] is True
    assert placements["vertical"]["manifest_present"] is False
