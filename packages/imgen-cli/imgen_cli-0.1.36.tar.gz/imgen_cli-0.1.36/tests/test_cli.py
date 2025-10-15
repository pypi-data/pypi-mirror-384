from __future__ import annotations

import json
from pathlib import Path

from imagemcp import ProjectPaths
from imagemcp.cli import main as cli_main
from imagemcp.storage import load_manifest


def test_cli_generate_and_select(tmp_path, capsys):
    project_root = tmp_path
    target_root = "assets"
    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "gen",
            "--slot",
            "hero",
            "--target-root",
            target_root,
            "--prompt",
            "Warm hero section illustration",
            "--generator",
            "mock",
            "--n",
            "2",
            "--json",
        ]
    )
    assert exit_code == 0
    first_output = json.loads(capsys.readouterr().out)
    session_id = first_output["sessionId"]
    assert first_output["galleryUrl"].startswith("http://")

    config_path = project_root / ".imagemcp" / "config.json"
    assert config_path.exists()
    config_data = json.loads(config_path.read_text("utf-8"))
    assert config_data["targetRoot"] == target_root

    target_path = project_root / target_root / "hero.png"
    assert target_path.exists()

    session_dir = project_root / ".imagemcp" / ".sessions" / f"hero_{session_id}"
    manifest_path = session_dir / "session.json"
    assert manifest_path.exists()

    manifest_data = json.loads(manifest_path.read_text("utf-8"))
    assert manifest_data["selectedIndex"] == 0
    assert len(manifest_data["history"]) == 1

    capsys.readouterr()  # Clear buffers
    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "select",
            "--target-root",
            target_root,
            "--slot",
            "hero",
            "--session",
            session_id,
            "--index",
            "1",
            "--json",
        ]
    )
    assert exit_code == 0
    second_output = json.loads(capsys.readouterr().out)
    assert second_output["selectedIndex"] == 1

    paths = ProjectPaths.create(Path(project_root), Path(target_root))
    manager_manifest = load_manifest(paths.manifest_path(session_dir))
    assert manager_manifest.selected_index == 1
    assert len(manager_manifest.history) == 2


def test_cli_missing_openrouter_api_key(tmp_path, capsys, monkeypatch):
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    exit_code = cli_main(
        [
            "--project-root",
            str(tmp_path),
            "gen",
            "--slot",
            "hero",
            "--prompt",
            "Checking API key handling",
            "--generator",
            "openrouter",
            "--n",
            "1",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "OpenRouter API key is missing" in captured.err
    assert "OPENROUTER_API_KEY" in captured.err
    assert str(tmp_path / ".env") in captured.err
    assert "no extra 'source .env' step" in captured.err
    assert "ask the user" in captured.err


def test_cli_models_lists_defaults(capsys):
    exit_code = cli_main(["models"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Provider: openrouter" in captured.out
    assert "google/gemini-2.5-flash-image-preview" in captured.out


def test_cli_models_unknown_provider(capsys):
    exit_code = cli_main(["models", "--provider", "bogus"])
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "Unknown provider" in captured.err


def test_cli_campaign_generate_emits_gallery_url(tmp_path, capsys, monkeypatch):
    project_root = tmp_path
    campaign_id = "camp_gallery"

    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "campaign",
            "init",
            campaign_id,
            "--objective",
            "Gallery smoke",
            "--placements",
            "meta_feed_square",
            "--json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "campaign",
            "route",
            "add",
            campaign_id,
            "main_story",
            "--summary",
            "Main story",
            "--prompt-template",
            "Test prompt",
            "--json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "campaign",
            "placement",
            "add",
            campaign_id,
            "meta_feed_square",
            "--variants",
            "1",
            "--json",
        ]
    )
    assert exit_code == 0
    capsys.readouterr()

    gallery_calls = []

    def fake_ensure_gallery_available(config, paths, host, port, force_restart):
        gallery_calls.append((config.project_id, host, port, force_restart))

    monkeypatch.setattr("imagemcp.cli._ensure_gallery_available", fake_ensure_gallery_available)

    exit_code = cli_main(
        [
            "--project-root",
            str(project_root),
            "campaign",
            "generate",
            campaign_id,
            "--generator",
            "mock",
            "--json",
        ]
    )
    assert exit_code == 0
    output = json.loads(capsys.readouterr().out)

    assert "gallery_url" in output
    assert output["gallery_url"].startswith("http://")
    assert gallery_calls
    assert gallery_calls[0][0]


def test_cli_invalid_model_guidance(tmp_path, capsys, monkeypatch):
    def fake_build_generator(output_dir, kind):
        raise RuntimeError(
            'OpenRouter API error 400: {"error":{"message":"flux-pro is not a valid model ID","code":400}}'
        )

    monkeypatch.setattr("imagemcp.cli.build_generator", fake_build_generator)

    exit_code = cli_main(
        [
            "--project-root",
            str(tmp_path),
            "gen",
            "--slot",
            "hero",
            "--prompt",
            "Check invalid model guidance",
            "--n",
            "1",
        ]
    )
    assert exit_code == 1
    captured = capsys.readouterr()
    assert "OpenRouter rejected the requested model" in captured.err
    assert "imgen models" in captured.err
