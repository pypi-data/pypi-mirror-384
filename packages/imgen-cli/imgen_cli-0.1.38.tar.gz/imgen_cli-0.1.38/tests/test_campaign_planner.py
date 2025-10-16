from __future__ import annotations

import io
import json
import shutil
import sys
import uuid
from pathlib import Path

import pytest

from imagemcp.campaign.planner import (
    CollectCampaignBriefPayload,
    PlanBatchGenerationPayload,
    PlanCampaignRoutesPayload,
    PlacementPlanInput,
    RoutePlanInput,
    collect_campaign_brief,
    normalize_collect_campaign_brief_payload,
    normalize_plan_batch_generation_payload,
    normalize_plan_campaign_routes_payload,
    plan_batch_generation,
    plan_campaign_routes,
)
from imagemcp.campaign.orchestrator import CliAction, execute_cli_actions


def test_collect_campaign_brief_reports_missing_fields():
    payload = CollectCampaignBriefPayload()
    result = collect_campaign_brief(payload)
    missing_fields = {item["field"] for item in result["missing"]}
    assert "campaign_id" in missing_fields
    assert "name" in missing_fields
    assert "objective" in missing_fields
    assert "routes" in missing_fields
    assert "placements" in missing_fields
    defaults = result["defaults"]
    assert defaults["variants"] == 2
    expected_tags = ["mock"] if defaults["generator"] == "mock" else []
    assert defaults["tags"] == expected_tags
    assert "placements" in result["catalog"]


def test_normalize_collect_campaign_brief_payload_accepts_json():
    normalized = normalize_collect_campaign_brief_payload(
        '{"brief": {"campaign_id": "spring_wave", "tags": ["mock", "qa"]}}'
    )
    assert isinstance(normalized, CollectCampaignBriefPayload)
    assert normalized.brief.campaign_id == "spring_wave"
    assert normalized.brief.tags == ["mock", "qa"]


def test_collect_campaign_brief_defaults_mock_tags():
    payload = CollectCampaignBriefPayload(
        brief=normalize_collect_campaign_brief_payload(
            '{"brief": {"generator": "mock"}}'
        ).brief
    )
    result = collect_campaign_brief(payload)
    assert result["defaults"]["generator"] == "mock"
    assert result["defaults"]["tags"] == ["mock"]


def test_plan_campaign_routes_emits_cli_actions(tmp_path: Path):
    payload = PlanCampaignRoutesPayload(
        campaign_id="spring_wave",
        name="Spring Wave",
        objective="Exercise the campaign toolchain",
        routes=[
            RoutePlanInput(
                route_id="ocean_luxury",
                name="Ocean Luxury",
                summary="Premium seaside visuals",
                prompt_template="Luxurious oceanfront aesthetic",
                prompt_tokens=["ocean", "luxury"],
            )
        ],
        placements=[
            PlacementPlanInput(placement_id="meta_square_awareness", template_id="meta_square_awareness")
        ],
        projectRoot=str(tmp_path),
        summary_only=True,
        tags=["mock", "qa"],
        generator="mock",
    )
    result = plan_campaign_routes(payload)
    cli_payload = result["cli"]
    actions = cli_payload["actions"]
    assert actions[0]["command"][:3] == ["imgen", "campaign", "init"]
    assert any(action["step"] == "generate" for action in actions)
    assert any(action["step"] == "status" for action in actions)
    assert cli_payload["requirements"]["command"] == "imgen"
    assert result["plan"]["generator"] == "mock"
    assert result["plan"]["provider"] == "mock"


def test_normalize_plan_campaign_routes_payload_accepts_dict():
    raw = {
        "campaign_id": "spring_wave",
        "routes": [
            {"route_id": "ocean_luxury"},
        ],
        "placements": [
            {"placement_id": "meta_square_awareness"},
        ],
    }
    normalized = normalize_plan_campaign_routes_payload(raw)
    assert isinstance(normalized, PlanCampaignRoutesPayload)
    assert normalized.routes[0].route_id == "ocean_luxury"
    assert normalized.placements[0].placement_id == "meta_square_awareness"


def test_plan_batch_generation_actions(tmp_path: Path):
    payload = PlanBatchGenerationPayload(
        campaign_id="spring_wave",
        routes=["ocean_luxury"],
        placements=["meta_square_awareness"],
        generator="mock",
        projectRoot=str(tmp_path),
    )
    result = plan_batch_generation(payload)
    actions = result["cli"]["actions"]
    steps = [action["step"] for action in actions]
    assert steps == ["batch-scaffold", "batch", "status", "export"]
    assert result["plan"]["generator"] == "mock"


def test_normalize_plan_batch_generation_payload_accepts_string():
    normalized = normalize_plan_batch_generation_payload(
        '{"campaign_id": "spring_wave", "routes": ["capsule"], "placements": ["meta"]}'
    )
    assert isinstance(normalized, PlanBatchGenerationPayload)
    assert normalized.routes == ["capsule"]


def test_execute_cli_actions_runs_commands(tmp_path: Path):
    ok_action = {
        "step": "echo",
        "description": "Echo text",
        "command": [sys.executable, "-c", "print('ok')"],
    }
    from io import StringIO

    buffer = StringIO()
    codes = execute_cli_actions([ok_action], project_root=str(tmp_path), stream=buffer)
    assert codes == [0]
    assert "step=echo" in buffer.getvalue()


def test_execute_cli_actions_stops_on_failure(tmp_path: Path):
    actions = [
        CliAction(step="pass", description="", command=[sys.executable, "-c", "import sys; sys.exit(0)"]),
        CliAction(step="fail", description="", command=[sys.executable, "-c", "import sys; sys.exit(3)"]),
        CliAction(step="skip", description="", command=[sys.executable, "-c", "import sys; sys.exit(0)"]),
    ]
    from io import StringIO

    buffer = StringIO()
    codes = execute_cli_actions(actions, project_root=str(tmp_path), stream=buffer)
    assert codes == [0, 3]


@pytest.mark.skipif(shutil.which("imgen") is None, reason="imgen CLI required for planner smoke test")
def test_campaign_planner_end_to_end_smoke(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    campaign_id = f"smoke_{uuid.uuid4().hex[:6]}"
    env_overrides = {
        "IMAGEMCP_DEFAULT_GENERATOR": "mock",
        "IMAGEMCP_DEFAULT_PROVIDER": "mock",
    }
    for key, value in env_overrides.items():
        monkeypatch.setenv(key, value)

    brief_response = collect_campaign_brief(
        normalize_collect_campaign_brief_payload({"brief": {"campaign_id": campaign_id}})
    )

    plan_request = {
        "campaign_id": campaign_id,
        "name": "Planner Smoke Test",
        "objective": "Verify planner orchestration in mock mode",
        "routes": [
            {
                "route_id": "ocean_luxury",
                "summary": "Luxury mock shots",
                "prompt_template": "Ocean luxury {{copy.headline}}",
                "prompt_tokens": ["mock", "luxury"],
            }
        ],
        "placements": [
            {"placement_id": "meta_square_awareness"},
        ],
        "generator": "mock",
        "summary_only": True,
        "projectRoot": str(tmp_path),
    }
    plan_response = plan_campaign_routes(
        normalize_plan_campaign_routes_payload(plan_request)
    )
    plan_actions = plan_response["cli"]["actions"]

    log_stream = io.StringIO()
    plan_codes = execute_cli_actions(
        plan_actions,
        project_root=str(tmp_path),
        env=env_overrides,
        stream=log_stream,
    )
    assert all(code == 0 for code in plan_codes), "Planner-generated commands must succeed"

    review_actions = [
        {
            "step": "review",
            "description": "Approve first variant",
            "command": [
                "imgen",
                "campaign",
                "review",
                campaign_id,
                "--route",
                "ocean_luxury",
                "--placement",
                "meta_square_awareness",
                "--variant",
                "0",
                "--state",
                "approved",
                "--notes",
                "Planner smoke approval",
                "--json",
            ],
        },
        {
            "step": "export",
            "description": "Export approved creatives",
            "command": [
                "imgen",
                "campaign",
                "export",
                campaign_id,
                "--platform",
                "meta_ads",
                "--include",
                "approved",
                "--summary-only",
            ],
        },
    ]
    review_codes = execute_cli_actions(
        review_actions,
        project_root=str(tmp_path),
        env=env_overrides,
        stream=log_stream,
    )
    assert review_codes == [0, 0], "Review/export commands should succeed"

    campaign_root = tmp_path / ".imagemcp" / "campaigns" / campaign_id
    placement_manifest_path = (
        campaign_root
        / "placements"
        / "meta_square_awareness"
        / "manifest.json"
    )
    manifest_data = json.loads(placement_manifest_path.read_text(encoding="utf-8"))
    route_entries = manifest_data.get("routes", [])
    assert route_entries, "Placement manifest must contain route entries"
    first_route_entry = route_entries[0]
    variants = first_route_entry.get("variants", [])
    assert variants, "Placement manifest must contain variants"
    first_variant = variants[0]
    provider = first_variant.get("provider") or first_variant.get("generator")
    review_state = first_variant.get("review_state") or first_variant.get("reviewState")
    variant_id = first_variant.get("variant_id")

    exports_dir = campaign_root / "exports" / "meta_ads"
    export_manifests = sorted(exports_dir.rglob("manifest.json"), key=lambda path: path.stat().st_mtime)
    assert export_manifests, "Export manifest should exist after export step"
    export_manifest_path = export_manifests[-1]
    export_manifest = json.loads(export_manifest_path.read_text(encoding="utf-8"))
    exported_pngs = [str(path.relative_to(tmp_path)) for path in export_manifest_path.parent.rglob("*.png")]

    report = {
        "campaign_id": campaign_id,
        "brief_missing_fields": [item["field"] for item in brief_response.get("missing", [])],
        "plan_steps": [
            {
                "step": action.get("step"),
                "command": action.get("command"),
                "returncode": code,
            }
            for action, code in zip(plan_actions, plan_codes)
        ],
        "follow_up_steps": [
            {
                "step": action.get("step"),
                "command": action.get("command"),
                "returncode": code,
            }
            for action, code in zip(review_actions, review_codes)
        ],
        "variant_summary": {
            "provider": provider,
            "review_state": review_state,
            "route_id": first_route_entry.get("route_id"),
            "variant_id": variant_id,
            "image_dir": str(
                (campaign_root / "images" / "ocean_luxury" / "meta_square_awareness").relative_to(tmp_path)
            ),
        },
        "export_manifest": {
            "path": str(export_manifest_path.relative_to(tmp_path)),
            "png_files": exported_pngs,
            "keys": sorted(export_manifest.keys()),
        },
        "log": log_stream.getvalue().splitlines(),
    }

    assert provider == "mock", "Expected mock provider in manifest"
    assert review_state == "approved", "Variant should be marked approved"
    assert exported_pngs, "Export should produce at least one PNG"

    print(json.dumps(report, indent=2))
