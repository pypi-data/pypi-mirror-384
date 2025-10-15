from __future__ import annotations

import json
from pathlib import Path

from typing import Dict

import pytest

from imagemcp.defaults import default_model_for_provider
from imagemcp.planner import (
    CollectContextPayload,
    KnownContext,
    PlanConstraints,
    PlanPayload,
    collect_context_questions,
    normalize_collect_context_payload,
    normalize_plan_payload,
    plan_image_job,
)


def _write_project_fixture(root: Path) -> Dict[str, object]:
    config_dir = root / ".imagemcp"
    sessions_dir = config_dir / ".sessions"
    session_dir = sessions_dir / "hero_20240101"
    config_dir.mkdir(parents=True, exist_ok=True)
    session_dir.mkdir(parents=True, exist_ok=True)

    config_data = {
        "schema": "imagemcp-project@1",
        "projectId": "test-project",
        "projectName": "Test Project",
        "targetRoot": "public/img",
        "gallery": {"host": "localhost", "port": 8765},
        "createdAt": "2024-01-01T00:00:00Z",
        "updatedAt": "2024-01-01T00:00:00Z",
    }
    (config_dir / "config.json").write_text(json.dumps(config_data), encoding="utf-8")

    manifest = {
        "schema": "image-slot-session@1",
        "slot": "hero",
        "sessionId": "hero-20240101",
        "targetPath": "public/img/hero.png",
        "sessionDir": ".imagemcp/.sessions/hero_20240101",
        "request": {"requestText": "Refresh hero", "createdBy": "cli"},
        "effective": {
            "prompt": "Refresh hero",
            "n": 1,
            "size": "1920x1080",
            "aspectRatio": None,
            "seed": None,
            "provider": "mock",
            "model": "mock-diffusion-v1",
            "providerOptions": {},
        },
        "images": [
            {
                "filename": "0.png",
                "mediaType": "image/png",
                "width": 1920,
                "height": 1080,
                "sha256": "deadbeef" * 8,
            }
        ],
        "selectedIndex": 0,
        "selectedPath": "public/img/hero.png",
        "history": [],
        "warnings": [],
        "timestamps": {
            "createdAt": "2024-01-01T00:00:00Z",
            "completedAt": "2024-01-01T00:00:00Z",
        },
    }
    (session_dir / "session.json").write_text(json.dumps(manifest), encoding="utf-8")
    return config_data


def test_collect_context_questions_identifies_missing_fields():
    payload = CollectContextPayload(requestText="Need homepage hero")
    result = collect_context_questions(payload)
    missing_fields = {item["field"] for item in result["missing"]}
    assert "slot" in missing_fields
    assert "projectRoot" in missing_fields
    defaults = result["defaults"]
    assert defaults["count"] == 3
    assert defaults["provider"] == "openrouter"
    assert defaults["model"] == "google/gemini-2.5-flash-image-preview"
    assert "size" not in defaults
    assert defaults["projectRoot"] == "."


def test_plan_image_job_respects_constraints():
    constraints = PlanConstraints(
        width=800,
        height=600,
        guidance="Use electric blues",
        provider="mock",
        model="mock-diffusion-v1",
    )
    payload = PlanPayload(
        slot="hero",
        requestText="Generate 2 bold hero illustrations",
        constraints=constraints,
        count=2,
        projectRoot="/tmp/project",
    )
    result = plan_image_job(payload)
    plan = result["plan"]
    assert plan["size"] == "800x600"
    assert plan["aspectRatio"] is None
    assert plan["n"] == 2
    command = result["cli"]["command"]
    assert "--size" in command
    assert "imgen" == command[0]
    assert command.count("--slot") == 1
    assert "--provider" in command
    assert "--model" in command
    assert plan["provider"] == "mock"
    assert result["cli"]["stdin"]["provider"] == "mock"
    assert result["cli"]["stdin"]["prompt"].startswith("Generate 2 bold hero illustrations")
    normalized_root = str(Path("/tmp/project").resolve())
    assert result["project"]["projectRoot"] == normalized_root
    assert result["cli"]["projectRoot"] == normalized_root
    assert any("auto-initialize" in note or "auto" in note for note in result["notes"])
    requirements = result["cli"]["requirements"]
    assert requirements["command"] == "imgen"
    assert requirements["minimumVersion"] == "0.1.0"
    assert requirements["setupResource"] == "setup://imgen-cli"
    assert requirements["installCommand"] == "pipx install imgen-cli"
    assert requirements["upgradeCommand"] == "pipx upgrade imgen-cli"
    assert requirements["pipxInstallCommand"] == "brew install pipx"
    assert any("setup://imgen-cli" in note for note in result["notes"])
    assert any("`pip install`" in note for note in result["notes"])
    assert any("brew install pipx" in note for note in result["notes"])
    assert any("setup://imgen-parameters" in note for note in result["notes"])


def test_plan_image_job_requires_geometry():
    payload = PlanPayload(
        slot="hero",
        requestText="Make something nice",
        constraints=PlanConstraints(),
    )
    with pytest.raises(ValueError):
        plan_image_job(payload)


def test_plan_image_job_defaults_provider_and_model_with_aspect_ratio():
    payload = PlanPayload(
        slot="hero",
        requestText="Create warm hero variations",
        constraints=PlanConstraints(aspectRatio="4:3"),
        projectRoot="/tmp/project",
    )
    result = plan_image_job(payload)
    plan = result["plan"]
    assert plan["size"] is None
    assert plan["aspectRatio"] == "4:3"
    assert plan["provider"] == "openrouter"
    assert plan["model"] == "google/gemini-2.5-flash-image-preview"
    command = result["cli"]["command"]
    assert "--aspect-ratio" in command
    assert "--provider" not in command
    assert "--project-root" in command
    assert "--model" in command
    assert result["cli"]["stdin"]["model"] == "google/gemini-2.5-flash-image-preview"
    assert "provider" not in result["cli"]["stdin"]
    assert plan["constraints"]["model"] == "google/gemini-2.5-flash-image-preview"
    assert any("Gemini 2.5" in note for note in result["notes"])


def test_plan_image_job_overrides_custom_model_to_gemini(tmp_path):
    constraints = PlanConstraints(width=512, height=512, model="other/unsupported-model")
    payload = PlanPayload(
        slot="hero",
        requestText="Override model",
        constraints=constraints,
        projectRoot=str(tmp_path),
    )
    result = plan_image_job(payload)
    expected_model = default_model_for_provider()
    plan = result["plan"]
    assert plan["model"] == expected_model
    assert plan["constraints"]["model"] == expected_model
    cli_stdin = result["cli"]["stdin"]
    assert cli_stdin["model"] == expected_model
    assert any("locking to" in note for note in result["notes"])


def test_normalize_plan_payload_accepts_string():
    raw = json.dumps(
        {
            "slot": "hero",
            "requestText": "String payload",
            "constraints": {
                "width": 512,
                "height": 512,
            },
            "projectRoot": "/projects/demo",
        }
    )
    payload = normalize_plan_payload(raw)
    assert isinstance(payload, PlanPayload)
    assert payload.slot == "hero"
    assert payload.constraints.width == 512
    assert payload.constraints.height == 512
    assert payload.projectRoot == "/projects/demo"


def test_normalize_collect_context_payload_accepts_string():
    raw = json.dumps(
        {
            "requestText": "Need hero",
            "known": {
                "slot": "hero",
                "constraints": {"aspectRatio": "16:9"},
            },
        }
    )
    payload = normalize_collect_context_payload(raw)
    assert isinstance(payload, CollectContextPayload)
    assert payload.known.slot == "hero"
    assert payload.known.constraints is not None
    assert payload.known.constraints.aspectRatio == "16:9"


def test_plan_image_job_suggests_existing_slot(tmp_path):
    _write_project_fixture(tmp_path)
    constraints = PlanConstraints(width=1920, height=1080)
    payload = PlanPayload(
        slot="hero-interior",
        requestText="Interior refresh for hero",
        constraints=constraints,
        projectRoot=str(tmp_path),
    )
    result = plan_image_job(payload)
    slot_info = result["slot"]
    assert slot_info["exists"] is False
    assert "hero" in slot_info["related"]
    assert slot_info["recommended"] == "hero"
    project_info = result["project"]
    assert "hero" in project_info["knownSlots"]
    assert project_info["galleryUrl"].endswith("slot=hero-interior")
    assert any("similar existing slots" in note for note in result["notes"])


def test_collect_context_questions_lists_known_slots(tmp_path):
    _write_project_fixture(tmp_path)
    payload = CollectContextPayload(known=KnownContext(projectRoot=str(tmp_path)))
    result = collect_context_questions(payload)
    assert any("Known slots" in note for note in result["notes"])
    assert any("Gallery preview" in note for note in result["notes"])
