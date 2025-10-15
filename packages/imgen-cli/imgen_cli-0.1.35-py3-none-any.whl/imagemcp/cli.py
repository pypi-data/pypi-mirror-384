from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
import webbrowser
import zipfile
from shutil import copy2
from datetime import datetime
from http.client import HTTPConnection
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence
from urllib.parse import quote_plus

import httpx

from . import (
    ProjectPaths,
    SessionManager,
    build_slot_index,
    make_session_id,
    ensure_project_config,
    register_project,
    discover_project_root,
)
from .campaign import (
    CampaignWorkspace,
    PlacementRef,
    CampaignRoute,
    CampaignStatusReport,
    PendingVariant,
    build_campaign_status,
)
from .campaign.setup import (
    add_placement_to_campaign,
    add_route_from_args,
    enrich_placement_geometry,
    ensure_campaign_exists,
    list_routes,
    load_route,
    remove_route,
    list_placements,
    get_placement,
    remove_placement_from_campaign,
)
from .campaign.schemas import (
    ExportCsv,
    ExportFile,
    ExportManifest,
    ExportRoute,
    ReviewState,
    BatchRoute,
    BatchPlacement,
    DeterministicBatchSpec,
)
from .campaign.runner import (
    DeterministicProviderError,
    execute_generation,
    plan_generation,
    plan_from_batch_spec,
)
from .config import CONFIG_DIR_NAME, CONFIG_FILENAME, ProjectConfig
from .gallery import serve_gallery
from .generator import GenerationResult, ProviderExecutionError, build_generator
from .defaults import DEFAULT_GENERATOR, DEFAULT_PROVIDER, available_models, default_model_for_provider
from .models import EffectiveParameters, SessionRequest
from .storage import InvalidPathError, list_manifests_for_slot
from .templates_catalog import (
    seed_default_placement_templates,
    load_default_placement_templates,
)


def _env_flag(name: str) -> bool:
    value = os.environ.get(name)
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


GALLERY_HOST = os.environ.get("IMAGEMCP_GALLERY_HOST", "localhost")
GALLERY_PORT = int(os.environ.get("IMAGEMCP_GALLERY_PORT", "8765"))
GALLERY_LAUNCH_TIMEOUT = float(os.environ.get("IMAGEMCP_GALLERY_START_TIMEOUT", "5"))
GALLERY_POLL_INTERVAL = float(os.environ.get("IMAGEMCP_GALLERY_POLL_INTERVAL", "0.2"))
GALLERY_ALWAYS_RESTART = _env_flag("IMAGEMCP_GALLERY_ALWAYS_RESTART")


def _project_config_path(project_root: Path) -> Path:
    return project_root / CONFIG_DIR_NAME / CONFIG_FILENAME


def _resolve_project_root(start: Path) -> Path:
    discovered = discover_project_root(start)
    if discovered:
        return discovered
    return start.resolve()


def _prepare_project(
    args: argparse.Namespace,
    *,
    allow_create: bool = True,
    project_name: Optional[str] = None,
    target_override: Optional[str] = None,
) -> tuple[ProjectConfig, ProjectPaths]:
    start_root = Path(getattr(args, "project_root", ".") or ".").resolve()
    project_root = _resolve_project_root(start_root)
    config_path = _project_config_path(project_root)
    if not config_path.exists() and not allow_create:
        raise RuntimeError(
            f"Project config not found at {config_path}. Run 'imgen init' or specify --target-root."
        )
    override = target_override or getattr(args, "target_root", None)
    config = ensure_project_config(project_root, target_root=override, project_name=project_name)
    register_project(config)
    target_root = override or config.target_root
    paths = ProjectPaths.create(config.project_root, Path(target_root))
    paths.ensure_directories()
    try:
        seed_default_placement_templates(paths.templates_root)
    except Exception as exc:
        print(f"[imagemcp] Warning: Failed to seed placement templates: {exc}", file=sys.stderr)
    _load_env_file(config.project_root)
    return config, paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="imgen", description="Image slot manager CLI")
    parser.add_argument(
        "--project-root",
        default=".",
        help="Project root directory (default: current directory)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen_parser = subparsers.add_parser("gen", help="Generate new variants for a slot")
    gen_parser.add_argument("--slot", required=True, help="Slot identifier (slug)")
    gen_parser.add_argument("--target-root", help="Override target asset root (default from project config)")
    gen_parser.add_argument("--prompt", help="Direct prompt string")
    gen_parser.add_argument(
        "--prompt-file",
        help="Path to prompt JSON input (use '-' for stdin)",
    )
    gen_parser.add_argument("--request-text", help="Human-readable request text")
    gen_parser.add_argument("--n", type=int, help="Number of variants to generate (default: 3)")
    size_group = gen_parser.add_mutually_exclusive_group()
    size_group.add_argument("--size", help="Image size (e.g. 1024x1024)")
    size_group.add_argument("--aspect-ratio", help="Aspect ratio (e.g. 16:9)")
    gen_parser.add_argument("--seed", type=int)
    gen_parser.add_argument("--provider", help="Provider id (e.g. openai)")
    gen_parser.add_argument(
        "--model",
        help="Model id (locked to google/gemini-2.5-flash-image-preview)",
    )
    gen_parser.add_argument("--session-hint", help="Hint to include in session id")
    gen_parser.add_argument(
        "--generator",
        default=None,
        help=(
            "Generator backend (default: openrouter; automatically switches to 'mock' when the provider is 'mock')"
        ),
    )
    gen_parser.add_argument(
        "--json",
        action="store_true",
        help="Emit JSON result to stdout",
    )
    gen_parser.add_argument(
        "--open-gallery",
        action="store_true",
        help="Include gallery URL in result",
    )
    gen_parser.add_argument(
        "--restart-gallery",
        action="store_true",
        help="Force-restart the gallery server for this run (also settable via IMAGEMCP_GALLERY_ALWAYS_RESTART)",
    )
    gen_parser.set_defaults(func=cmd_generate)

    init_parser = subparsers.add_parser("init", help="Initialize project configuration")
    init_parser.add_argument("--project-root", default=".")
    init_parser.add_argument("--target-root", help="Target asset root (default: public/img)")
    init_parser.add_argument("--project-name", help="Human-friendly project name")
    init_parser.add_argument("--json", action="store_true")
    init_parser.set_defaults(func=cmd_init)

    select_parser = subparsers.add_parser("select", help="Promote a specific variant")
    select_parser.add_argument("--target-root")
    select_parser.add_argument("--slot", help="Slot id (optional if session uniquely identifies)")
    select_parser.add_argument("--session", required=True, help="Session id")
    select_parser.add_argument("--index", required=True, type=int, help="Variant index")
    select_parser.add_argument("--json", action="store_true")
    select_parser.set_defaults(func=cmd_select)

    slots_parser = subparsers.add_parser("slots", help="Slot operations")
    slots_sub = slots_parser.add_subparsers(dest="slots_command", required=True)
    slots_list_parser = slots_sub.add_parser("list", help="List slots")
    slots_list_parser.add_argument("--target-root")
    slots_list_parser.add_argument("--json", action="store_true")
    slots_list_parser.set_defaults(func=cmd_slots_list)

    sessions_parser = subparsers.add_parser("sessions", help="Session operations")
    sessions_sub = sessions_parser.add_subparsers(dest="sessions_command", required=True)
    sessions_list_parser = sessions_sub.add_parser("list", help="List sessions for a slot")
    sessions_list_parser.add_argument("--target-root")
    sessions_list_parser.add_argument("--slot", required=True)
    sessions_list_parser.add_argument("--json", action="store_true")
    sessions_list_parser.set_defaults(func=cmd_sessions_list)

    session_info_parser = sessions_sub.add_parser("info", help="Show session manifest contents")
    session_info_parser.add_argument("--target-root")
    session_info_parser.add_argument("--slot", required=True)
    session_info_parser.add_argument("--session", required=True)
    session_info_parser.add_argument("--json", action="store_true")
    session_info_parser.set_defaults(func=cmd_session_info)

    gallery_parser = subparsers.add_parser("gallery", help="Gallery server")
    gallery_sub = gallery_parser.add_subparsers(dest="gallery_command", required=True)
    gallery_serve_parser = gallery_sub.add_parser("serve", help="Run the local gallery web server")
    gallery_serve_parser.add_argument("--target-root")
    gallery_serve_parser.add_argument("--host", default="127.0.0.1")
    gallery_serve_parser.add_argument("--port", type=int, default=8765)
    gallery_serve_parser.add_argument("--open-browser", action="store_true")
    gallery_serve_parser.set_defaults(func=cmd_gallery_serve)

    gallery_ensure_parser = gallery_sub.add_parser("ensure", help="Ensure the gallery server is running in the background")
    gallery_ensure_parser.add_argument("--target-root")
    gallery_ensure_parser.add_argument("--host", default=GALLERY_HOST)
    gallery_ensure_parser.add_argument("--port", type=int, default=GALLERY_PORT)
    gallery_ensure_parser.add_argument("--restart", action="store_true", help="Force a restart even if a server is detected")
    gallery_ensure_parser.set_defaults(func=cmd_gallery_ensure)

    gallery_stop_parser = gallery_sub.add_parser("stop", help="Terminate the background gallery server if it is running")
    gallery_stop_parser.add_argument("--target-root")
    gallery_stop_parser.add_argument("--host", default=GALLERY_HOST)
    gallery_stop_parser.add_argument("--port", type=int, default=GALLERY_PORT)
    gallery_stop_parser.set_defaults(func=cmd_gallery_stop)

    models_parser = subparsers.add_parser("models", help="List supported providers and models")
    models_parser.add_argument("--provider", help="Filter results to a provider id")
    models_parser.set_defaults(func=cmd_models)

    provider_parser = subparsers.add_parser("provider", help="Provider utilities")
    provider_sub = provider_parser.add_subparsers(dest="provider_command", required=True)

    provider_openrouter_parser = provider_sub.add_parser("openrouter", help="OpenRouter tools")
    provider_openrouter_sub = provider_openrouter_parser.add_subparsers(
        dest="openrouter_command",
        required=True,
    )
    provider_openrouter_status = provider_openrouter_sub.add_parser(
        "status",
        help="Check OpenRouter API key usage and limits",
    )
    provider_openrouter_status.add_argument("--json", action="store_true")
    provider_openrouter_status.set_defaults(func=cmd_provider_openrouter_status)

    campaign_parser = subparsers.add_parser("campaign", help="Campaign workflow commands")
    campaign_sub = campaign_parser.add_subparsers(dest="campaign_command", required=True)

    campaign_init_parser = campaign_sub.add_parser("init", help="Scaffold a new campaign workspace")
    campaign_init_parser.add_argument("campaign_id", help="Campaign identifier (lowercase slug)")
    campaign_init_parser.add_argument("--name", help="Campaign display name")
    campaign_init_parser.add_argument("--objective", help="Objective to seed the brief with")
    campaign_init_parser.add_argument(
        "--brief-file",
        help="Optional YAML/JSON file containing initial brief data",
    )
    campaign_init_parser.add_argument(
        "--placements",
        help="Comma-separated placement template ids to include",
    )
    campaign_init_parser.add_argument(
        "--metadata",
        nargs="*",
        default=(),
        help="Additional asset metadata entries (key=value)",
    )
    campaign_init_parser.add_argument(
        "--tags",
        help="Comma-separated tag slugs",
    )
    campaign_init_parser.add_argument("--json", action="store_true")
    campaign_init_parser.set_defaults(func=cmd_campaign_init)

    campaign_route_parser = campaign_sub.add_parser("route", help="Route management")
    campaign_route_sub = campaign_route_parser.add_subparsers(dest="route_command", required=True)
    campaign_route_add = campaign_route_sub.add_parser("add", help="Add or update a campaign route")
    campaign_route_add.add_argument("campaign_id", help="Campaign id")
    campaign_route_add.add_argument("route_id", help="Route id (slug)")
    campaign_route_add.add_argument("--name", help="Route display name")
    campaign_route_add.add_argument("--summary", help="Route summary")
    campaign_route_add.add_argument("--source", help="Route source (manual/ai/catalog)")
    campaign_route_add.add_argument("--prompt-template", help="Prompt template body")
    campaign_route_add.add_argument(
        "--prompt",
        dest="prompt_tokens",
        action="append",
        help="Prompt token to append (repeatable)",
    )
    campaign_route_add.add_argument(
        "--copy",
        dest="copy_tokens",
        action="append",
        help="Copy token to append (repeatable)",
    )
    campaign_route_add.add_argument("--notes", help="Optional notes")
    campaign_route_add.add_argument(
        "--input",
        help="Read prompt template from file ('-' for stdin)",
    )
    campaign_route_add.add_argument("--json", action="store_true")
    campaign_route_add.set_defaults(func=cmd_campaign_route_add)

    campaign_route_list = campaign_route_sub.add_parser("list", help="List campaign routes")
    campaign_route_list.add_argument("campaign_id", help="Campaign identifier")
    campaign_route_list.add_argument("--json", action="store_true")
    campaign_route_list.set_defaults(func=cmd_campaign_route_list)

    campaign_route_show = campaign_route_sub.add_parser("show", help="Show route details")
    campaign_route_show.add_argument("campaign_id", help="Campaign identifier")
    campaign_route_show.add_argument("route_id", help="Route id")
    campaign_route_show.add_argument("--json", action="store_true")
    campaign_route_show.set_defaults(func=cmd_campaign_route_show)

    campaign_route_remove = campaign_route_sub.add_parser("remove", help="Remove a route")
    campaign_route_remove.add_argument("campaign_id", help="Campaign identifier")
    campaign_route_remove.add_argument("route_id", help="Route id")
    campaign_route_remove.add_argument(
        "--delete-files",
        action="store_true",
        help="Delete the entire route directory including stored templates/assets",
    )
    campaign_route_remove.add_argument("--json", action="store_true")
    campaign_route_remove.set_defaults(func=cmd_campaign_route_remove)

    campaign_placement_parser = campaign_sub.add_parser("placement", help="Placement management")
    campaign_placement_sub = campaign_placement_parser.add_subparsers(dest="placement_command", required=True)
    campaign_placement_add = campaign_placement_sub.add_parser(
        "add", help="Add or update a placement reference in campaign.yaml"
    )
    campaign_placement_add.add_argument("campaign_id", help="Campaign id")
    campaign_placement_add.add_argument("placement_id", help="Placement id or override slug")
    campaign_placement_add.add_argument(
        "--template",
        help="Placement template id if different from placement id",
    )
    campaign_placement_add.add_argument(
        "--variants",
        type=int,
        help="Preferred variant count override",
    )
    campaign_placement_add.add_argument(
        "--provider",
        help="Provider override for this placement",
    )
    campaign_placement_add.add_argument(
        "--copy",
        dest="copy_tokens",
        action="append",
        help="Placement copy token (repeatable)",
    )
    campaign_placement_add.add_argument("--notes", help="Optional notes")
    campaign_placement_add.add_argument("--json", action="store_true")
    campaign_placement_add.set_defaults(func=cmd_campaign_placement_add)

    campaign_placement_list = campaign_placement_sub.add_parser(
        "list", help="List placements declared in campaign.yaml"
    )
    campaign_placement_list.add_argument("campaign_id", help="Campaign identifier")
    campaign_placement_list.add_argument("--json", action="store_true")
    campaign_placement_list.set_defaults(func=cmd_campaign_placement_list)

    campaign_placement_show = campaign_placement_sub.add_parser(
        "show", help="Show placement details"
    )
    campaign_placement_show.add_argument("campaign_id", help="Campaign identifier")
    campaign_placement_show.add_argument("placement_id", help="Placement id")
    campaign_placement_show.add_argument("--json", action="store_true")
    campaign_placement_show.set_defaults(func=cmd_campaign_placement_show)

    campaign_placement_remove = campaign_placement_sub.add_parser(
        "remove", help="Remove a placement from campaign.yaml"
    )
    campaign_placement_remove.add_argument("campaign_id", help="Campaign identifier")
    campaign_placement_remove.add_argument("placement_id", help="Placement id")
    campaign_placement_remove.add_argument("--json", action="store_true")
    campaign_placement_remove.set_defaults(func=cmd_campaign_placement_remove)

    campaign_status_parser = campaign_sub.add_parser("status", help="Summarize campaign progress")
    campaign_status_parser.add_argument("campaign_id", help="Campaign identifier")
    campaign_status_parser.add_argument(
        "--pending-limit",
        type=int,
        default=20,
        help="Number of pending items to list when not using --json (default: 20)",
    )
    campaign_status_parser.add_argument("--json", action="store_true")
    campaign_status_parser.set_defaults(func=cmd_campaign_status)

    campaign_generate_parser = campaign_sub.add_parser("generate", help="Generate variants for campaign placements")
    campaign_generate_parser.add_argument("campaign_id", help="Campaign identifier")
    campaign_generate_parser.add_argument(
        "--routes",
        help="Comma-separated route ids to generate (default: all)"
    )
    campaign_generate_parser.add_argument(
        "--placements",
        help="Comma-separated placement ids or template ids (default: all)",
    )
    campaign_generate_parser.add_argument("--variants", type=int, help="Override variant count per placement")
    campaign_generate_parser.add_argument("--provider", help="Override provider id")
    campaign_generate_parser.add_argument("--generator", help="Generator backend override (mock/openrouter)")
    campaign_generate_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a single-line summary when not using --json",
    )
    campaign_generate_parser.add_argument(
        "--restart-gallery",
        action="store_true",
        help="Force-restart the gallery server after generation",
    )
    campaign_generate_parser.add_argument("--json", action="store_true")
    campaign_generate_parser.set_defaults(func=cmd_campaign_generate)

    campaign_batch_parser = campaign_sub.add_parser("batch", help="Execute batch spec for deterministic runs")
    campaign_batch_parser.add_argument("campaign_id", help="Campaign identifier")
    campaign_batch_parser.add_argument("--spec", help="Path to batch spec (default: campaign batch.yaml)")
    campaign_batch_parser.add_argument("--generator", help="Generator backend override")
    campaign_batch_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a single-line summary when not using --json",
    )
    campaign_batch_parser.add_argument("--json", action="store_true")
    campaign_batch_parser.set_defaults(func=cmd_campaign_batch)

    campaign_review_parser = campaign_sub.add_parser("review", help="Update review state for a variant")
    campaign_review_parser.add_argument("campaign_id", help="Campaign identifier")
    campaign_review_parser.add_argument("--route", required=True, help="Route id")
    campaign_review_parser.add_argument("--placement", required=True, help="Placement id")
    campaign_review_parser.add_argument("--variant", type=int, required=True, help="Variant index (0-based)")
    campaign_review_parser.add_argument(
        "--state",
        choices=["pending", "approved", "revise"],
        required=True,
        help="Review state to apply",
    )
    campaign_review_parser.add_argument("--notes", help="Optional review notes")
    campaign_review_parser.add_argument("--json", action="store_true")
    campaign_review_parser.set_defaults(func=cmd_campaign_review)

    campaign_export_parser = campaign_sub.add_parser("export", help="Export campaign bundle for a platform")
    campaign_export_parser.add_argument("campaign_id", help="Campaign identifier")
    campaign_export_parser.add_argument("--platform", required=True, help="Platform id (e.g., meta_ads)")
    campaign_export_parser.add_argument(
        "--include",
        default="approved",
        help="Comma-separated review states to include (default: approved)",
    )
    campaign_export_parser.add_argument(
        "--output",
        help="Optional zip file path; defaults to the generated export directory",
    )
    campaign_export_parser.add_argument(
        "--summary-only",
        action="store_true",
        help="Print a single-line summary when not using --json",
    )
    campaign_export_parser.add_argument("--json", action="store_true")
    campaign_export_parser.set_defaults(func=cmd_campaign_export)

    campaign_batch_scaffold_parser = campaign_sub.add_parser(
        "batch-scaffold",
        help="Create or update a deterministic batch spec for a campaign",
    )
    campaign_batch_scaffold_parser.add_argument("campaign_id", help="Campaign identifier")
    campaign_batch_scaffold_parser.add_argument(
        "--routes",
        help="Comma-separated route ids to include (default: all discovered routes)",
    )
    campaign_batch_scaffold_parser.add_argument(
        "--placements",
        help="Comma-separated placement ids to include (default: all placements in campaign.yaml)",
    )
    campaign_batch_scaffold_parser.add_argument(
        "--variants",
        type=int,
        help="Variants per placement (default: campaign variant defaults)",
    )
    campaign_batch_scaffold_parser.add_argument(
        "--provider",
        help="Provider override for the batch (default: campaign default provider)",
    )
    campaign_batch_scaffold_parser.add_argument(
        "--output",
        help="Destination file path (default: campaign batch.yaml)",
    )
    campaign_batch_scaffold_parser.add_argument("--json", action="store_true")
    campaign_batch_scaffold_parser.set_defaults(func=cmd_campaign_batch_scaffold)

    templates_parser = subparsers.add_parser("templates", help="Template catalog utilities")
    templates_sub = templates_parser.add_subparsers(dest="templates_command", required=True)
    templates_list_parser = templates_sub.add_parser("list", help="List available placement templates")
    templates_list_parser.add_argument("--platform", help="Filter by platform id")
    templates_list_parser.add_argument("--id", help="Filter by template id substring")
    templates_list_parser.add_argument("--json", action="store_true")
    templates_list_parser.set_defaults(func=cmd_templates_list)

    return parser


def _probe_gallery(host: str, port: int, timeout: float = 0.5) -> bool:
    """Return True if the gallery server responds successfully."""
    conn: Optional[HTTPConnection] = None
    try:
        conn = HTTPConnection(host, port, timeout=timeout)
        conn.request("GET", "/")
        response = conn.getresponse()
        response.read()
        return 200 <= response.status < 500
    except OSError:
        return False
    finally:
        if conn is not None:
            try:
                conn.close()
            except OSError:
                pass


def _gallery_pid_path(paths: ProjectPaths) -> Path:
    return paths.target_root / ".imagemcp-gallery.pid"


def _global_gallery_state_path() -> Path:
    return Path.home() / CONFIG_DIR_NAME / "gallery.json"


def _load_env_file(project_root: Path) -> None:
    env_path = project_root / ".env"
    try:
        data = env_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    except OSError as exc:
        print(f"[imagemcp] Warning: Unable to read {env_path}: {exc}", file=sys.stderr)
        return
    for raw_line in data.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export "):].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _read_gallery_pid(paths: ProjectPaths) -> Optional[int]:
    try:
        data = _gallery_pid_path(paths).read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not data:
        return None
    try:
        return int(data)
    except ValueError:
        return None


def _write_gallery_pid(paths: ProjectPaths, pid: int) -> None:
    path = _gallery_pid_path(paths)
    path.write_text(str(pid), encoding="utf-8")


def _clear_gallery_pid(paths: ProjectPaths) -> None:
    path = _gallery_pid_path(paths)
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def _read_global_gallery_state() -> Optional[Dict[str, str]]:
    state_path = _global_gallery_state_path()
    try:
        return json.loads(state_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        return None


def _write_global_gallery_state(paths: ProjectPaths, pid: int) -> None:
    state_path = _global_gallery_state_path()
    payload = {
        "pid": str(pid),
        "projectRoot": str(paths.project_root),
        "targetRoot": str(paths.target_root),
    }
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        state_path.write_text(json.dumps(payload), encoding="utf-8")
    except PermissionError:
        pass


def _clear_global_gallery_state() -> None:
    state_path = _global_gallery_state_path()
    try:
        state_path.unlink()
    except FileNotFoundError:
        pass
    except PermissionError:
        pass


def _launch_gallery_background(config: ProjectConfig, paths: ProjectPaths, host: str, port: int) -> subprocess.Popen[bytes]:
    try:
        target_root = paths.target_root.relative_to(paths.project_root).as_posix()
    except ValueError:
        target_root = str(paths.target_root)
    project_root = str(paths.project_root)
    cmd = [
        sys.executable,
        "-m",
        "imagemcp.cli",
        "--project-root",
        project_root,
        "gallery",
        "serve",
        "--target-root",
        target_root,
        "--host",
        host,
        "--port",
        str(port),
    ]
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    _write_gallery_pid(paths, process.pid)
    _write_global_gallery_state(paths, process.pid)
    return process


def _terminate_existing_gallery(paths: ProjectPaths, host: str, port: int) -> None:
    pid = _read_gallery_pid(paths)
    state = _read_global_gallery_state()
    candidate_pids = []
    if pid is not None:
        candidate_pids.append(pid)
    if state and state.get("pid"):
        try:
            candidate_pids.append(int(state["pid"]))
        except ValueError:
            pass
    if not candidate_pids:
        return
    for candidate in candidate_pids:
        try:
            os.kill(candidate, signal.SIGTERM)
        except ProcessLookupError:
            continue
        except PermissionError:
            print(
                f"[imagemcp] Warning: Unable to terminate existing gallery process {candidate} due to permissions.",
                file=sys.stderr,
            )
            continue
    deadline = time.time() + GALLERY_LAUNCH_TIMEOUT
    while time.time() < deadline:
        if not _probe_gallery(host, port):
            break
        time.sleep(GALLERY_POLL_INTERVAL)
    _clear_gallery_pid(paths)
    _clear_global_gallery_state()


def _ensure_gallery_available(
    config: ProjectConfig,
    paths: ProjectPaths,
    host: str,
    port: int,
    force_restart: bool = False,
) -> None:
    state = _read_global_gallery_state()
    if state:
        if state.get("projectRoot") != str(paths.project_root) or state.get("targetRoot") != str(paths.target_root):
            force_restart = True
    if force_restart:
        _terminate_existing_gallery(paths, host, port)
    if _probe_gallery(host, port):
        _register_project_with_gallery(config, host, port)
        return
    print(
        f"[imagemcp] No gallery server detected at http://{host}:{port}/. Starting one in the background...",
        file=sys.stderr,
    )
    try:
        process = _launch_gallery_background(config, paths, host, port)
    except OSError as exc:
        print(f"[imagemcp] Warning: Failed to launch gallery server: {exc}", file=sys.stderr)
        return
    deadline = time.time() + GALLERY_LAUNCH_TIMEOUT
    while time.time() < deadline:
        if _probe_gallery(host, port):
            print(
                f"[imagemcp] Gallery server is now available at http://{host}:{port}/ (pid {process.pid}).",
                file=sys.stderr,
            )
            return
        time.sleep(GALLERY_POLL_INTERVAL)
    print(
        f"[imagemcp] Warning: Gallery server did not become ready at http://{host}:{port}/."
        " It may still be starting; check logs if the endpoint remains unreachable.",
        file=sys.stderr,
    )


def _register_project_with_gallery(config: ProjectConfig, host: str, port: int) -> None:
    payload = {
        "projectId": config.project_id,
        "projectName": config.project_name,
        "projectRoot": str(config.project_root),
        "targetRoot": config.target_root,
    }
    try:
        conn = HTTPConnection(host, port, timeout=1.5)
        conn.request(
            "POST",
            "/api/register",
            body=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        conn.getresponse().read()
    except Exception:
        pass
    finally:
        try:
            conn.close()
        except Exception:
            pass


def cmd_generate(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args)
    except InvalidPathError as exc:
        return _fail(str(exc))
    except RuntimeError as exc:
        return _fail(str(exc))
    manager = SessionManager(paths)

    session_id = make_session_id(args.session_hint)
    ctx = manager.create_context(args.slot, session_id)
    manager.ensure_session_dir(ctx)

    payload = _load_prompt_payload(args.prompt, args.prompt_file)
    if not payload.prompt:
        return _fail("A prompt is required via --prompt or --prompt-file")

    count = args.n if args.n is not None else payload.count or 3
    if count <= 0:
        return _fail("--n must be at least 1")

    size = args.size or payload.size
    aspect_ratio = args.aspect_ratio or payload.aspect_ratio
    seed = args.seed if args.seed is not None else payload.seed
    provider = args.provider or payload.provider or DEFAULT_PROVIDER
    default_model = default_model_for_provider(provider)
    requested_model = args.model or payload.model
    manual_warnings: list[str] = []
    if provider == "mock":
        model = requested_model or default_model
    else:
        if requested_model and requested_model != default_model:
            manual_warnings.append(
                "Requested model '{requested}' is not supported; using '{locked}' instead.".format(
                    requested=requested_model,
                    locked=default_model,
                )
            )
        model = default_model
    generator_name = (
        (args.generator if args.generator else None)
        or payload.generator
        or ("mock" if provider == "mock" else DEFAULT_GENERATOR)
    )

    request_text = args.request_text or payload.request_text or f"Generate {count} variants for {args.slot}"

    try:
        generator = build_generator(ctx.session_dir, generator_name)
    except Exception as exc:  # pragma: no cover - depends on generator backend
        return _handle_generator_exception(exc, config, json_mode=args.json)

    try:
        generation: GenerationResult = generator.generate(
            payload.prompt,
            count,
            size=size,
            aspect_ratio=aspect_ratio,
            seed=seed,
            provider=provider,
            model=model,
            provider_options=payload.provider_options,
        )
    except Exception as exc:  # pragma: no cover - depends on generator backend
        context = {
            "slot": args.slot,
            "generator": generator_name,
            "provider": provider,
            "model": model,
        }
        return _handle_generator_exception(exc, config, context=context, json_mode=args.json)

    if manual_warnings:
        generation.warnings[:0] = manual_warnings

    request = SessionRequest(request_text=request_text, created_by="cli")
    effective = EffectiveParameters(
        prompt=payload.prompt,
        n=count,
        size=size,
        aspect_ratio=aspect_ratio,
        seed=seed,
        provider=provider,
        model=model,
        generator=generator_name,
        provider_options=payload.provider_options,
    )

    manifest = manager.build_manifest(
        ctx,
        request=request,
        effective=effective,
        image_artifacts=generation.images,
        warnings=generation.warnings,
        auto_selected_index=0,
    )
    manager.promote_variant(ctx, manifest, 0)

    if hasattr(generator, "close"):
        try:
            generator.close()
        except Exception:  # pragma: no cover - defensive cleanup
            pass

    force_restart_gallery = args.restart_gallery or GALLERY_ALWAYS_RESTART
    _ensure_gallery_available(config, paths, GALLERY_HOST, GALLERY_PORT, force_restart_gallery)

    gallery_url = _default_gallery_url(config.project_id, args.slot)
    result = {
        "ok": True,
        "slot": args.slot,
        "sessionId": session_id,
        "selectedIndex": manifest.selected_index,
        "selectedPath": manifest.selected_path,
        "sessionDir": str(ctx.session_dir.relative_to(paths.project_root)),
        "warnings": manifest.warnings,
        "galleryUrl": gallery_url,
        "projectId": config.project_id,
        "projectName": config.project_name,
        "targetRoot": config.target_root,
        "generator": generator_name,
    }
    if args.open_gallery:
        webbrowser.open(gallery_url, new=2)

    if args.json:
        _print_json(result)
    else:
        _print_human_result(result)
    return 0


def cmd_init(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root or ".").resolve()
    target_root = args.target_root
    project_name = args.project_name
    config = ensure_project_config(project_root, target_root=target_root, project_name=project_name)
    register_project(config)
    payload = {
        "ok": True,
        "projectId": config.project_id,
        "projectName": config.project_name,
        "projectRoot": str(config.project_root),
        "targetRoot": config.target_root,
        "configPath": str(config.config_path()),
    }
    if args.json:
        _print_json(payload)
    else:
        print(f"Project '{config.project_name}' initialized at {payload['configPath']}")
        print(f"Target root: {config.target_root}")
        print(f"Project id: {config.project_id}")
    return 0


def cmd_select(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    manager = SessionManager(paths)
    try:
        slot_id = args.slot or _infer_slot(paths, args.session)
    except LookupError as exc:
        return _fail(str(exc))
    ctx = manager.create_context(slot_id, args.session)
    if not ctx.manifest_path.exists():
        return _fail("Session manifest not found")
    manifest = manager.read_manifest(ctx)
    if args.index < 0 or args.index >= len(manifest.images):
        return _fail("Variant index out of range")
    manager.promote_variant(ctx, manifest, args.index)
    result = {
        "ok": True,
        "slot": ctx.slot,
        "sessionId": ctx.session_id,
        "selectedIndex": manifest.selected_index,
        "selectedPath": manifest.selected_path,
        "projectId": config.project_id,
        "projectName": config.project_name,
    }
    if args.json:
        _print_json(result)
    else:
        _print_human_result(result)
    return 0


def cmd_slots_list(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    summaries = build_slot_index(paths)
    if args.json:
        payload = {
            "projectId": config.project_id,
            "projectName": config.project_name,
            "targetRoot": config.target_root,
            "slots": {
                slot: {
                    "sessionCount": summary.session_count,
                    "selectedPath": summary.selected_path,
                    "selectedIndex": summary.selected_index,
                    "lastUpdated": summary.last_updated.isoformat() if summary.last_updated else None,
                    "warnings": summary.warnings,
                }
                for slot, summary in summaries.items()
            },
        }
        _print_json(payload)
    else:
        if not summaries:
            print("No slots found.")
            return 0
        for slot, summary in summaries.items():
            last_updated = summary.last_updated.isoformat() if summary.last_updated else "-"
            print(
                f"{slot}: {summary.selected_path or 'n/a'} (#{summary.selected_index if summary.selected_index is not None else '-'})"
                f", sessions={summary.session_count}, updated={last_updated}"
            )
    return 0


def cmd_sessions_list(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    manifests = list_manifests_for_slot(paths, args.slot)
    manifests.sort(key=lambda m: m.created_at)
    if args.json:
        payload = {
            "projectId": config.project_id,
            "projectName": config.project_name,
            "targetRoot": config.target_root,
            "slot": args.slot,
            "sessions": [
                {
                    "sessionId": manifest.session_id,
                    "selectedIndex": manifest.selected_index,
                    "selectedPath": manifest.selected_path,
                    "createdAt": manifest.created_at.isoformat(),
                    "completedAt": manifest.completed_at.isoformat(),
                    "warnings": manifest.warnings,
                }
                for manifest in manifests
            ],
        }
        _print_json(payload)
    else:
        if not manifests:
            print("No sessions found for slot.")
            return 0
        for manifest in manifests:
            print(f"{manifest.session_id}: selected #{manifest.selected_index} -> {manifest.selected_path}")
    return 0


def cmd_session_info(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    manager = SessionManager(paths)
    ctx = manager.create_context(args.slot, args.session)
    if not ctx.manifest_path.exists():
        return _fail("Session manifest not found")
    manifest = manager.read_manifest(ctx)
    if args.json:
        payload = manifest.to_dict()
        payload["projectId"] = config.project_id
        payload["projectName"] = config.project_name
        _print_json(payload)
    else:
        print(json.dumps(manifest.to_dict(), indent=2))
    return 0


def cmd_gallery_serve(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(
            args,
            allow_create=True,
            project_name=getattr(args, "project_name", None),
            target_override=args.target_root,
        )
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    url = f"http://{args.host}:{args.port}/"
    if args.open_browser:
        webbrowser.open(url, new=2)
    try:
        serve_gallery(config, paths, host=args.host, port=args.port)
    except OSError as exc:
        return _fail(f"Gallery failed to start: {exc}")
    return 0


def cmd_gallery_ensure(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    host = args.host or GALLERY_HOST
    port = args.port or GALLERY_PORT
    force_restart = args.restart or GALLERY_ALWAYS_RESTART
    _ensure_gallery_available(config, paths, host, port, force_restart)
    return 0


def cmd_gallery_stop(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))
    host = args.host or GALLERY_HOST
    port = args.port or GALLERY_PORT
    _terminate_existing_gallery(paths, host, port)
    return 0


def cmd_models(args: argparse.Namespace) -> int:
    models = available_models()
    if args.provider:
        provider = args.provider.strip().lower()
        options = models.get(provider)
        if not options:
            known = ", ".join(sorted(models)) or "(none)"
            return _fail(f"Unknown provider '{provider}'. Known providers: {known}")
        print(f"Provider: {provider}")
        for model in options:
            print(f"  - {model}")
        return 0
    for provider in sorted(models):
        print(f"Provider: {provider}")
        for model in models[provider]:
            print(f"  - {model}")
    return 0


def cmd_provider_openrouter_status(args: argparse.Namespace) -> int:
    try:
        config, _ = _prepare_project(args)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        env_hint = config.project_root / ".env"
        return _fail(
            "OPENROUTER_API_KEY not found. Add it to your environment or include it in "
            f"{env_hint} before running this command."
        )

    base_url = os.environ.get("IMAGEMCP_OPENROUTER_BASE_URL", "https://openrouter.ai").rstrip("/")
    if base_url.endswith("/api/v1"):
        key_url = f"{base_url}/key"
    else:
        key_url = f"{base_url}/api/v1/key"

    timeout = float(os.environ.get("IMAGEMCP_OPENROUTER_TIMEOUT", "60"))
    headers = {"Authorization": f"Bearer {api_key}"}

    try:
        response = httpx.get(key_url, headers=headers, timeout=timeout)
    except httpx.RequestError as exc:
        return _fail(f"Failed to reach {key_url}: {exc}")

    if response.status_code != 200:
        snippet = _clip_text(response.text or "", limit=800)
        return _fail(
            f"OpenRouter key endpoint returned HTTP {response.status_code}. Body: {snippet}"
        )

    try:
        payload = response.json()
    except ValueError as exc:
        return _fail(f"Failed to decode OpenRouter key response as JSON: {exc}")

    data = payload.get("data") or {}
    status = {
        "label": data.get("label"),
        "usage": data.get("usage"),
        "limit": data.get("limit"),
        "is_free_tier": data.get("is_free_tier"),
    }
    rate_limit = data.get("rate_limit") or {}
    if rate_limit:
        status["rate_limit"] = rate_limit

    result = {
        "provider": "openrouter",
        "endpoint": key_url,
        "status": status,
    }

    if getattr(args, "json", False):
        print(json.dumps(result, indent=2))
        return 0

    label = status.get("label") or "(no label)"
    usage = status.get("usage")
    limit = status.get("limit")
    free_tier = status.get("is_free_tier")

    print(f"OpenRouter key label: {label}")
    if usage is not None:
        print(f"Credits used: {usage}")
    if limit is None:
        print("Credit limit: unlimited")
    else:
        print(f"Credit limit: {limit}")
    if free_tier is not None:
        print(f"Free tier account: {'yes' if free_tier else 'no'}")

    if rate_limit:
        rpm = rate_limit.get("requests_per_minute")
        rpd = rate_limit.get("requests_per_day")
        if rpm or rpd:
            print("Rate limits:")
            if rpm:
                print(f"  - Requests per minute: {rpm}")
            if rpd:
                print(f"  - Requests per day: {rpd}")

    print("Docs: https://openrouter.ai/docs/api-reference/limits")
    return 0


def cmd_campaign_init(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args)
    except (InvalidPathError, RuntimeError, ValueError) as exc:
        return _fail(str(exc))

    campaign_id = args.campaign_id.strip()
    workspace = CampaignWorkspace(paths, campaign_id)

    brief_data: Dict[str, Any] = {}
    if args.brief_file:
        try:
            brief_data = _load_structured_data(args.brief_file)
        except Exception as exc:  # noqa: BLE001
            return _fail(f"Failed to load brief file: {exc}")
    objective = args.objective or brief_data.get("objective")
    if not objective:
        objective = "TODO: update campaign objective"
    brief_data.setdefault("objective", objective)

    name = args.name or campaign_id.replace("_", " ").title()
    tags = [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()]
    try:
        assets = _parse_metadata(args.metadata or [])
    except ValueError as exc:
        return _fail(str(exc))

    placement_refs: list[PlacementRef] = []
    if args.placements:
        placements = [item.strip() for item in args.placements.split(",") if item.strip()]
        placement_refs = [
            enrich_placement_geometry(PlacementRef(template_id=slug))
            for slug in placements
        ]

    existing = workspace.config_path.exists()
    try:
        config_obj = workspace.ensure_default_config(name=name, brief=brief_data)
    except ValueError as exc:
        return _fail(f"Invalid campaign brief: {exc}")

    updated_brief = config_obj.brief.model_copy(update=brief_data)
    config_obj = config_obj.model_copy(update={
        "name": name,
        "tags": tags,
        "brief": updated_brief,
        "placements": placement_refs or config_obj.placements,
        "assets": assets or config_obj.assets,
    })
    workspace.save_config(config_obj)

    result = {
        "project_root": str(config.project_root),
        "campaign_id": campaign_id,
        "config_path": str(workspace.config_path),
        "created": not existing,
        "placements": [ref.effective_id for ref in config_obj.placements],
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        status = "Created" if not existing else "Updated"
        print(f"{status} campaign '{campaign_id}' at {workspace.config_path}")
        if config_obj.placements:
            print("Placements:")
            for ref in config_obj.placements:
                print(f"  - {ref.effective_id}")
    return 0


def cmd_campaign_route_add(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    workspace.ensure_scaffold()
    prompt_template = args.prompt_template or _read_text_payload(args.input)
    route = add_route_from_args(
        workspace,
        args.route_id.strip(),
        name=args.name,
        summary=args.summary,
        prompt_template=prompt_template,
        source=args.source,
        prompt_tokens=args.prompt_tokens,
        copy_tokens=args.copy_tokens,
        notes=args.notes,
    )
    payload = {
        "campaign_id": args.campaign_id,
        "route_id": route.route_id,
        "route_path": str(workspace.route_path(route.route_id)),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Saved route '{route.route_id}' to {payload['route_path']}")
    return 0


def cmd_campaign_route_list(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    routes = list_routes(workspace)
    rows = []
    for route in routes:
        rows.append(
            {
                "route_id": route.route_id,
                "name": route.name,
                "source": route.source.value if hasattr(route.source, "value") else str(route.source),
                "summary": route.summary,
            }
        )

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        if not rows:
            print("No routes defined.")
            return 0
        header = f"{'route_id':<24} {'source':<10} {'name':<30} {'summary':<48}"
        print(header)
        print("-" * len(header))
        for row in rows:
            print(
                f"{row['route_id']:<24} {row['source']:<10} {row['name']:<30} {_truncate_text(row['summary'], 48):<48}"
            )
        print(f"Total: {len(rows)} routes")
    return 0


def cmd_campaign_route_show(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    try:
        route = load_route(workspace, args.route_id)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    payload = route.model_dump(mode="python", exclude_none=True)
    payload["route_path"] = str(workspace.route_path(route.route_id))
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_key_values(payload)
    return 0


def cmd_campaign_route_remove(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    try:
        removed_path = remove_route(
            workspace,
            args.route_id.strip(),
            delete_assets=args.delete_files,
        )
    except FileNotFoundError as exc:
        return _fail(str(exc))

    payload = {
        "campaign_id": args.campaign_id,
        "route_id": args.route_id.strip(),
        "removed_path": str(removed_path),
        "deleted_assets": bool(args.delete_files),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        verb = "Deleted" if args.delete_files else "Removed"
        print(f"{verb} route '{args.route_id}' from campaign '{args.campaign_id}'")
    return 0


def cmd_campaign_placement_add(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    workspace.ensure_scaffold()
    placement = add_placement_to_campaign(
        workspace,
        args.placement_id.strip(),
        template_id=args.template,
        variants=args.variants,
        provider=args.provider,
        copy_tokens=args.copy_tokens,
        notes=args.notes,
    )
    payload = {
        "campaign_id": args.campaign_id,
        "placement_id": placement.effective_id,
        "template_id": placement.template_id,
        "variants": placement.variants,
        "config_path": str(workspace.config_path),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(
            f"Updated campaign '{args.campaign_id}' with placement '{placement.effective_id}'"
        )
    return 0


def cmd_campaign_placement_list(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    placements = list_placements(workspace)
    rows = []
    for placement in placements:
        rows.append(
            {
                "placement_id": placement.effective_id,
                "template_id": placement.template_id,
                "variants": placement.variants,
                "provider": placement.provider,
            }
        )

    if args.json:
        print(json.dumps(rows, indent=2))
    else:
        if not rows:
            print("No placements defined.")
            return 0
        header = f"{'placement':<28} {'template':<28} {'variants':<9} {'provider':<12}"
        print(header)
        print("-" * len(header))
        for row in rows:
            variants = row["variants"] if row["variants"] is not None else "-"
            provider = row["provider"] or "-"
            print(
                f"{row['placement_id']:<28} {row['template_id']:<28} {str(variants):<9} {provider:<12}"
            )
        print(f"Total: {len(rows)} placements")
    return 0


def cmd_campaign_placement_show(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    try:
        placement = get_placement(workspace, args.placement_id.strip())
    except FileNotFoundError as exc:
        return _fail(str(exc))

    payload = placement.model_dump(mode="python", exclude_none=True)
    payload["placement_id"] = placement.effective_id
    payload["campaign_yaml"] = str(workspace.config_path)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        _print_key_values(payload)
    return 0


def cmd_campaign_placement_remove(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    placement_id = args.placement_id.strip()
    try:
        remove_placement_from_campaign(workspace, placement_id)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    payload = {
        "campaign_id": args.campaign_id,
        "placement_id": placement_id,
        "config_path": str(workspace.config_path),
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Removed placement '{placement_id}' from campaign '{args.campaign_id}'")
    return 0


def cmd_campaign_status(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    try:
        report = build_campaign_status(workspace)
    except Exception as exc:  # pragma: no cover - defensive guard
        return _fail(f"Failed to compute campaign status: {exc}")

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        pending_limit = getattr(args, "pending_limit", 20) or 0
        if pending_limit < 0:
            pending_limit = 0
        _print_campaign_status(report, pending_limit=pending_limit)
    return 0


def cmd_campaign_batch_scaffold(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    workspace = CampaignWorkspace(paths, args.campaign_id)
    try:
        ensure_campaign_exists(workspace)
    except FileNotFoundError as exc:
        return _fail(str(exc))

    workspace.ensure_scaffold()

    config = workspace.load_config()

    selected_routes = _split_csv(args.routes)
    selected_placements = _split_csv(args.placements)

    routes_index: Dict[str, CampaignRoute] = {
        route.route_id: route for route in workspace.iter_routes() or []
    }
    if not routes_index and config.routes:
        for seed in config.routes:
            routes_index.setdefault(
                seed.route_id,
                CampaignRoute(
                    route_id=seed.route_id,
                    name=seed.name,
                    summary=seed.summary,
                    source="seed",
                    prompt_template="\n".join(seed.prompt_tokens) or seed.summary,
                    prompt_tokens=seed.prompt_tokens,
                    copy_tokens=seed.copy_tokens,
                ),
            )

    route_ids = selected_routes or list(routes_index)
    if not route_ids:
        return _fail("No routes available. Add routes before scaffolding a batch spec.")

    batch_routes: list[BatchRoute] = []
    for route_id in route_ids:
        route = routes_index.get(route_id)
        if route is None:
            return _fail(f"Route '{route_id}' not found. Use 'imgen campaign route add' first.")
        batch_routes.append(
            BatchRoute(
                route_id=route.route_id,
                prompt=route.prompt_template,
                copy_tokens=list(route.copy_tokens or []),
            )
        )

    placements = config.placements or []
    if selected_placements:
        placements = [
            placement
            for placement in placements
            if placement.effective_id in selected_placements
        ]
    if not placements:
        return _fail("No placements defined in campaign.yaml. Use 'imgen campaign placement add'.")

    batch_placements: list[BatchPlacement] = []
    for placement in placements:
        placement_id = placement.override_id or placement.template_id
        batch_placements.append(
            BatchPlacement(
                placement_id=placement_id,
                template_id=placement.template_id,
                provider=placement.provider,
                variants=placement.variants,
            )
        )

    variants_per = args.variants if args.variants and args.variants > 0 else config.variant_defaults.count
    provider = args.provider or config.default_provider

    created_at = datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    run_id = f"{config.campaign_id}_{created_at.replace('-', '').replace(':', '').replace('T', '').replace('Z', '')}"

    spec = DeterministicBatchSpec(
        campaign_id=config.campaign_id,
        run_id=run_id,
        created_at=created_at,
        routes=batch_routes,
        placements=batch_placements,
        variants_per_placement=variants_per,
        provider=provider,
        provider_params={},
        output_root="images/",
    )

    destination: Optional[Path] = None
    if args.output:
        destination = Path(args.output).expanduser()

    saved_path = workspace.save_batch_spec(spec, destination)
    payload = {
        "campaign_id": config.campaign_id,
        "batch_spec_path": str(saved_path),
        "routes": [route.route_id for route in batch_routes],
        "placements": [placement.placement_id for placement in batch_placements],
    }
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"Wrote batch spec to {saved_path}")
    return 0


def cmd_templates_list(args: argparse.Namespace) -> int:
    templates = load_default_placement_templates()
    platform_filter = args.platform.lower() if args.platform else None
    id_filter = args.id.lower() if args.id else None

    filtered = []
    for template in templates:
        template_id = str(template.get("template_id", ""))
        platform = str(template.get("platform", ""))
        if platform_filter and platform.lower() != platform_filter:
            continue
        if id_filter and id_filter not in template_id.lower():
            continue
        filtered.append(template)

    if args.json:
        print(json.dumps(filtered, indent=2))
        return 0

    if not filtered:
        print("No templates found.")
        return 0

    header = f"{'template_id':<28} {'platform':<10} {'format':<28} {'size':<12}"
    print(header)
    print("-" * len(header))
    for template in filtered:
        template_id = template.get("template_id", "")
        platform = template.get("platform", "")
        fmt = template.get("format", "")
        dims = template.get("dimensions") or {}
        size = f"{dims.get('width', '?')}x{dims.get('height', '?')}"
        print(f"{template_id:<28} {platform:<10} {fmt:<28} {size:<12}")
    print(f"Total: {len(filtered)} templates")
    return 0


def cmd_campaign_generate(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    campaign_id = args.campaign_id.strip()
    workspace = CampaignWorkspace(paths, campaign_id)
    if not workspace.config_path.exists():
        return _fail(f"Campaign '{campaign_id}' is not initialized. Run 'imgen campaign init {campaign_id}' first.")

    try:
        campaign_config = workspace.load_config()
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Failed to read campaign config: {exc}")

    workspace.ensure_scaffold()

    routes = None
    if args.routes:
        routes = [item.strip() for item in args.routes.split(",") if item.strip()]
    placements = None
    if args.placements:
        placements = [item.strip() for item in args.placements.split(",") if item.strip()]

    variants_override = args.variants
    provider_override = args.provider

    try:
        plans = plan_generation(
            workspace,
            campaign_config,
            routes=routes,
            placements=placements,
            variants_override=variants_override,
            provider_override=provider_override,
        )
    except DeterministicProviderError as exc:
        return _fail(str(exc))
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Failed to build generation plan: {exc}")

    try:
        stats = execute_generation(
            workspace,
            plans,
            generator_kind=args.generator,
        )
    except ProviderExecutionError as exc:
        context = {"campaign_id": campaign_id}
        return _handle_generator_exception(exc, config, context=context, json_mode=args.json)
    except Exception as exc:  # noqa: BLE001
        downgrade = _detect_missing_provider_exception(exc)
        if downgrade:
            return _fail(downgrade)
        return _fail(f"Campaign generation failed: {exc}")

    result = {
        "campaign_id": campaign_id,
        "generated_variants": stats.generated,
        "warnings": stats.warnings,
    }

    force_restart_gallery = getattr(args, "restart_gallery", False) or GALLERY_ALWAYS_RESTART
    _ensure_gallery_available(config, paths, GALLERY_HOST, GALLERY_PORT, force_restart_gallery)
    gallery_url = _default_campaign_gallery_url(config.project_id, campaign_id)
    result["gallery_url"] = gallery_url

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if getattr(args, "summary_only", False):
            message = f"{campaign_id}: generated {stats.generated} variants | gallery: {gallery_url}"
            if stats.warnings:
                message += f" (warnings: {len(stats.warnings)})"
            print(message)
        else:
            print(f"Generated {stats.generated} variants for campaign '{campaign_id}'")
            if stats.warnings:
                print("Warnings:")
                for warning in stats.warnings:
                    print(f"  - {warning}")
            print(f"View campaign in gallery: {gallery_url}")
    return 0


def cmd_campaign_batch(args: argparse.Namespace) -> int:
    try:
        config, paths = _prepare_project(args)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    campaign_id = args.campaign_id.strip()
    workspace = CampaignWorkspace(paths, campaign_id)
    spec_path = Path(args.spec) if args.spec else workspace.batch_spec_path()
    if not spec_path.exists():
        return _fail(f"Batch spec not found at {spec_path}")

    try:
        spec = workspace.load_batch_spec(spec_path)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Failed to load batch spec: {exc}")

    if spec.campaign_id != campaign_id:
        return _fail(
            f"Batch spec campaign_id '{spec.campaign_id}' does not match requested campaign '{campaign_id}'"
        )

    workspace.ensure_scaffold()

    try:
        plans = plan_from_batch_spec(workspace, spec)
    except DeterministicProviderError as exc:
        return _fail(str(exc))
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Failed to build batch generation plan: {exc}")

    try:
        stats = execute_generation(
            workspace,
            plans,
            generator_kind=args.generator,
        )
    except ProviderExecutionError as exc:
        context = {"campaign_id": campaign_id, "batch_spec": str(spec_path)}
        return _handle_generator_exception(exc, config, context=context, json_mode=args.json)
    except Exception as exc:  # noqa: BLE001
        downgrade = _detect_missing_provider_exception(exc)
        if downgrade:
            return _fail(downgrade)
        return _fail(f"Batch generation failed: {exc}")

    log_path = workspace.logs_dir / f"batch-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jsonl"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("w", encoding="utf-8") as fh:
        for event in stats.events:
            fh.write(json.dumps(event))
            fh.write("\n")

    result = {
        "campaign_id": campaign_id,
        "generated_variants": stats.generated,
        "log_path": str(log_path),
        "warnings": stats.warnings,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if getattr(args, "summary_only", False):
            message = f"{campaign_id}: batch generated {stats.generated} variants (log {log_path})"
            if stats.warnings:
                message += f"; warnings: {len(stats.warnings)}"
            print(message)
        else:
            print(f"Batch run completed for '{campaign_id}' -> {stats.generated} variants")
            print(f"Log: {log_path}")
            if stats.warnings:
                print("Warnings:")
                for warning in stats.warnings:
                    print(f"  - {warning}")
    return 0


def cmd_campaign_review(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    campaign_id = args.campaign_id.strip()
    workspace = CampaignWorkspace(paths, campaign_id)
    manifest_path = workspace.placement_manifest_path(args.placement)
    if not manifest_path.exists():
        return _fail(f"Manifest not found for placement '{args.placement}'")

    try:
        manifest = workspace.load_manifest(args.placement)
    except Exception as exc:  # noqa: BLE001
        return _fail(f"Failed to load manifest: {exc}")

    target_route = None
    for route in manifest.routes:
        if route.route_id == args.route:
            target_route = route
            break
    if target_route is None:
        return _fail(f"Route '{args.route}' not present in manifest")

    target_variant = None
    for variant in target_route.variants:
        if variant.index == args.variant:
            target_variant = variant
            break
    if target_variant is None:
        return _fail(f"Variant index {args.variant} not found for route '{args.route}'")

    state = ReviewState(args.state)
    target_variant.review_state = state
    if args.notes is not None:
        target_variant.review_notes = args.notes

    manifest.updated_at = datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    workspace.save_manifest(manifest)

    result = {
        "campaign_id": campaign_id,
        "placement_id": args.placement,
        "route_id": args.route,
        "variant_index": args.variant,
        "state": state.value,
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(
            f"Updated review state for {campaign_id} route={args.route} placement={args.placement} variant={args.variant} -> {state.value}"
        )
    return 0


def cmd_campaign_export(args: argparse.Namespace) -> int:
    try:
        _, paths = _prepare_project(args, allow_create=False)
    except (InvalidPathError, RuntimeError) as exc:
        return _fail(str(exc))

    campaign_id = args.campaign_id.strip()
    workspace = CampaignWorkspace(paths, campaign_id)
    include_states: List[ReviewState] = []
    for state in (args.include or "").split(","):
        if not state.strip():
            continue
        try:
            include_states.append(ReviewState(state.strip()))
        except ValueError:
            return _fail(f"Invalid review state '{state}' in --include")
    if not include_states:
        include_states = [ReviewState.APPROVED]

    export_id = f"{args.platform}-{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}"
    manifest_path = workspace.export_manifest_path(args.platform, export_id)
    export_root = manifest_path.parent
    export_root.mkdir(parents=True, exist_ok=True)

    placements: set[str] = set()
    routes_map: Dict[str, ExportRoute] = {}
    export_files: List[ExportFile] = []
    csv_records: List[tuple[str, str, str, str]] = []

    for manifest in workspace.iter_manifests() or []:
        placements.add(manifest.placement_id)
        for route in manifest.routes:
            routes_map.setdefault(route.route_id, ExportRoute(route_id=route.route_id, summary=route.summary))
            for variant in route.variants:
                if variant.review_state not in include_states:
                    continue
                source_path = workspace.root / variant.file
                if not source_path.exists():
                    continue
                relative_path = Path(variant.file)
                target_path = export_root / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                copy2(source_path, target_path)
                checksum = _sha256_of(target_path)
                export_files.append(
                    ExportFile(
                        path=str(relative_path).replace("\\", "/"),
                        placement_id=manifest.placement_id,
                        variant_id=variant.variant_id,
                        review_state=variant.review_state,
                        checksum=checksum,
                    )
                )
                csv_records.append(
                    (
                        variant.variant_id,
                        manifest.placement_id,
                        route.route_id,
                        str(relative_path).replace("\\", "/"),
                    )
                )

    csv_relative = Path(args.platform) / f"{args.platform}_upload.csv"
    csv_path = export_root / csv_relative
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["variant_id", "placement_id", "route_id", "file"])
        for record in csv_records:
            writer.writerow(record)

    csv_entry = ExportCsv(
        name=f"{args.platform}_upload",
        path=str(csv_relative).replace("\\", "/"),
        profile=f"{args.platform}_v1",
        checksum=_sha256_of(csv_path),
        row_count=len(csv_records),
    )

    export_manifest = ExportManifest(
        campaign_id=campaign_id,
        platform=args.platform,
        export_id=export_id,
        generated_at=datetime.utcnow().replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ"),
        routes=list(routes_map.values()),
        placements=sorted(placements),
        include_states=include_states,
        files=export_files,
        csv_files=[csv_entry],
    )

    workspace.save_export_manifest(export_manifest, manifest_path)

    output_zip = None
    if args.output:
        output_zip = Path(args.output)
        output_zip.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in export_root.rglob("*"):
                if path.is_dir():
                    continue
                archive.write(path, arcname=path.relative_to(export_root))

    result = {
        "campaign_id": campaign_id,
        "platform": args.platform,
        "export_id": export_id,
        "export_dir": str(export_root),
        "manifest": str(manifest_path),
        "output_zip": str(output_zip) if output_zip else None,
        "files": len(export_files),
    }
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if getattr(args, "summary_only", False):
            message = f"{campaign_id}: exported {len(export_files)} files to {export_root}"
            if output_zip:
                message += f" (zip {output_zip})"
            print(message)
        else:
            print(f"Export bundle created at {export_root}")
            print(f"Manifest: {manifest_path}")
            if output_zip:
                print(f"Zip: {output_zip}")
    return 0


def _load_prompt_payload(prompt: Optional[str], prompt_file: Optional[str]) -> "PromptPayload":
    prompt_text = prompt
    request_text: Optional[str] = None
    provider_options: Dict[str, Any] = {}
    provider: Optional[str] = None
    model: Optional[str] = None
    size_override: Optional[str] = None
    aspect_override: Optional[str] = None
    seed_override: Optional[int] = None
    count_override: Optional[int] = None
    generator_override: Optional[str] = None

    if prompt_file:
        raw = _read_input(prompt_file)
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                prompt_text = prompt_text or parsed.get("prompt")
                request_text = parsed.get("requestText")
                provider_options_data = parsed.get("providerOptions", {}) or {}
                if isinstance(provider_options_data, dict):
                    provider_options = provider_options_data
                prompt_text = prompt_text or parsed.get("text")
                provider = parsed.get("provider") or provider
                model = parsed.get("model") or model
                generator_override = parsed.get("generator") or generator_override
                size_override = parsed.get("size") or size_override
                aspect_override = parsed.get("aspectRatio") or aspect_override
                seed_value = parsed.get("seed")
                if isinstance(seed_value, int):
                    seed_override = seed_value
                count_value = parsed.get("n") or parsed.get("count")
                if isinstance(count_value, int):
                    count_override = count_value
            elif isinstance(parsed, str):
                prompt_text = prompt_text or parsed
        except json.JSONDecodeError:
            prompt_text = prompt_text or raw

    return PromptPayload(
        prompt=prompt_text or "",
        request_text=request_text,
        provider_options=provider_options,
        provider=provider,
        model=model,
        generator=generator_override,
        size=size_override,
        aspect_ratio=aspect_override,
        seed=seed_override,
        count=count_override,
    )


def _read_input(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


def _infer_slot(paths: ProjectPaths, session_id: str) -> str:
    if not paths.sessions_root.exists():
        raise LookupError("No session data available")
    matches = []
    for directory in paths.sessions_root.iterdir():
        if not directory.is_dir():
            continue
        try:
            slug, rest = directory.name.split("_", 1)
        except ValueError:
            continue
        if rest == session_id:
            matches.append(slug)
    if not matches:
        raise LookupError("Session id not found")
    if len(matches) > 1:
        raise LookupError("Multiple slots share this session id; specify --slot")
    return matches[0]


def _default_gallery_url(project_id: str, slot: str) -> str:
    project_param = quote_plus(project_id)
    slot_param = quote_plus(slot)
    return f"http://{GALLERY_HOST}:{GALLERY_PORT}/?project={project_param}&slot={slot_param}"


def _default_campaign_gallery_url(project_id: str, campaign_id: str) -> str:
    project_param = quote_plus(project_id)
    campaign_param = quote_plus(campaign_id)
    return f"http://{GALLERY_HOST}:{GALLERY_PORT}/?project={project_param}&campaign={campaign_param}"


def _print_json(payload: Any) -> None:
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")


def _print_key_values(data: Dict[str, Any]) -> None:
    for key in sorted(data):
        value = data[key]
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, indent=2)
            print(f"{key}:")
            for line in rendered.splitlines():
                print(f"  {line}")
        else:
            print(f"{key}: {value}")


def _truncate_text(value: Optional[str], limit: int = 48) -> str:
    if not value:
        return ""
    if len(value) <= limit:
        return value
    return value[: limit - 1] + "…"


def _print_human_result(payload: Dict[str, Any]) -> None:
    if payload.get("ok"):
        slot = payload.get("slot")
        path = payload.get("selectedPath")
        print(f"Slot '{slot}' promoted {path}")
        if payload.get("warnings"):
            print("Warnings:")
            for warning in payload["warnings"]:
                print(f"  - {warning}")
        if payload.get("galleryUrl"):
            print(f"Gallery: {payload['galleryUrl']}")
    else:
        print(payload)


def _print_campaign_status(report: CampaignStatusReport, *, pending_limit: int = 20) -> None:
    totals = report.totals
    print(f"Campaign {report.campaign_id}")
    print(
        "Routes: {routes} | Placements: {placements} | Generated: {generated}/{expected} | Pending: {pending} | Extra: {extra}".format(
            routes=totals.routes,
            placements=totals.placements,
            generated=totals.generated_variants,
            expected=totals.expected_variants,
            pending=totals.pending_variants,
            extra=totals.extra_generated,
        )
    )

    print()
    print("Placements:")
    if not report.placements:
        print("  (no placements found)")
    else:
        for placement in report.placements:
            template_note = ""
            if placement.template_id and placement.template_id != placement.placement_id:
                template_note = f" (template {placement.template_id})"
            print(
                "  - {placement}{template}: {generated}/{expected} generated, pending {pending}, extra {extra}".format(
                    placement=placement.placement_id,
                    template=template_note,
                    generated=placement.generated_variants,
                    expected=placement.expected_variants,
                    pending=placement.pending_variants,
                    extra=placement.extra_generated,
                )
            )
            manifest_note = "present" if placement.manifest_present else "missing"
            if placement.manifest_path:
                print(f"    manifest: {manifest_note} ({placement.manifest_path})")
            else:
                print(f"    manifest: {manifest_note}")
            total_routes = totals.routes or max(placement.routes_with_output, len(placement.routes_missing))
            print(
                "    routes with output: {done}/{total}".format(
                    done=placement.routes_with_output,
                    total=total_routes,
                )
            )
            if placement.routes_missing:
                preview = ", ".join(placement.routes_missing[:5])
                if len(placement.routes_missing) > 5:
                    preview += ", ..."
                print(f"    routes pending: {preview}")

    if report.routes:
        print()
        print("Routes:")
        for route in report.routes:
            summary = "  - {route}: {generated}/{expected} generated".format(
                route=route.route_id,
                generated=route.total_generated,
                expected=route.total_expected,
            )
            if route.total_pending:
                summary += f" (pending {route.total_pending})"
            print(summary)
            for placement in route.placements:
                if (
                    placement.expected_variants == 0
                    and placement.generated_variants == 0
                    and not placement.pending_variants
                    and not placement.extra_generated
                ):
                    continue
                detail = "    - {placement}: {generated}/{expected}".format(
                    placement=placement.placement_id,
                    generated=placement.generated_variants,
                    expected=placement.expected_variants,
                )
                if placement.pending_variants:
                    detail += " pending " + _format_variant_list(placement.pending_variants)
                if placement.extra_generated:
                    detail += " | extra " + _format_variant_list(placement.extra_generated)
                print(detail)

    if report.pending and pending_limit != 0:
        print()
        print("Next pending variants:")
        for entry in _summarize_pending(report.pending, limit=pending_limit):
            print(f"  - {entry}")

    if report.orphan_files:
        print()
        print("Orphan files:")
        for path in report.orphan_files:
            print(f"  - {path}")

    if report.missing_manifests:
        print()
        print("Placements missing manifests:")
        for path in report.missing_manifests:
            print(f"  - {path}")


def _format_variant_index(index: int) -> str:
    return f"v{index + 1:03d}"


def _format_variant_list(indices: Sequence[int], limit: int = 3) -> str:
    if not indices:
        return ""
    tokens = [_format_variant_index(idx) for idx in indices[:limit]]
    if len(indices) > limit:
        tokens.append("...")
    return ", ".join(tokens)


def _summarize_pending(pending: Sequence[PendingVariant], *, limit: int) -> List[str]:
    if limit <= 0:
        return []
    ordered = sorted(pending, key=lambda item: (item.placement_id, item.route_id, item.variant_index))
    lines: List[str] = []
    max_items = min(limit, len(ordered))
    for item in ordered[:max_items]:
        lines.append(
            "{placement} / {route} -> {variant}".format(
                placement=item.placement_id,
                route=item.route_id,
                variant=_format_variant_index(item.variant_index),
            )
        )
    remaining = len(ordered) - len(lines)
    if remaining > 0:
        lines.append(f"... ({remaining} more)")
    return lines


def _fail(message: str) -> int:
    print(message, file=sys.stderr)
    return 1


def _handle_generator_exception(
    exc: Exception,
    config: ProjectConfig,
    context: Optional[Dict[str, object]] = None,
    *,
    json_mode: bool = False,
) -> int:
    downgrade = _detect_missing_provider_exception(exc)
    if downgrade:
        return _fail(downgrade)
    if isinstance(exc, ProviderExecutionError):
        if context:
            exc.attach_context(context)
        message = _render_provider_error(exc)
        return _fail(message)

    message = str(exc)
    env_hint = config.project_root / ".env"
    key_notice = "OpenRouter API key is missing"
    if key_notice in message:
        guidance = (
            "OpenRouter API key is missing. Set OPENROUTER_API_KEY in your environment.\n"
            f"Add a line like OPENROUTER_API_KEY=sk-... to {env_hint} and rerun the command; no extra 'source .env' step is required because the CLI reloads the file automatically.\n"
            "If the key is unavailable, ask the user to provide a valid OpenRouter API token before continuing."
        )
        return _fail(guidance)
    if "not a valid model ID" in message:
        guidance = (
            "OpenRouter rejected the requested model. Use the default `google/gemini-2.5-flash-image-preview` or consult "
            "resource setup://imgen-parameters. Run `imgen models` to list supported options."
        )
        return _fail(guidance)
    return _fail(f"Generator error ({exc.__class__.__name__}): {message}")


def _render_provider_error(exc: ProviderExecutionError) -> str:
    provider = exc.provider or "unknown"
    generator = exc.generator or "unknown"
    context = exc.context or {}

    location_bits: list[str] = []
    campaign_id = context.get("campaign_id")
    if campaign_id:
        location_bits.append(f"campaign '{campaign_id}'")
    slot = context.get("slot")
    if slot:
        location_bits.append(f"slot '{slot}'")
    route_id = context.get("route_id")
    if route_id:
        location_bits.append(f"route '{route_id}'")
    placement_id = context.get("placement_id")
    if placement_id:
        location_bits.append(f"placement '{placement_id}'")
    variant_index = context.get("variant_index")
    if isinstance(variant_index, int):
        location_bits.append(f"variant {variant_index + 1:03d}")

    header = f"Provider '{provider}' failed via generator '{generator}'"
    if location_bits:
        header += " while processing " + ", ".join(location_bits)
    header += "."

    lines = [header]

    reason = context.get("reason")
    if reason:
        lines.append(f"Failure reason: {reason}")

    message = str(exc).strip()
    if message:
        lines.append(f"Error detail: {message}")

    model_id = context.get("model")
    if model_id:
        lines.append(f"Model: {model_id}")

    attempts_count = context.get("attempts")
    text_only_attempts = context.get("text_only_attempts")
    max_text_only_retries = context.get("max_text_only_retries")
    if attempts_count or text_only_attempts or max_text_only_retries:
        retry_bits: list[str] = []
        if attempts_count:
            retry_bits.append(f"attempts={attempts_count}")
        if text_only_attempts:
            retry_bits.append(f"text-only responses={text_only_attempts}")
        if max_text_only_retries is not None:
            retry_bits.append(f"auto-retry limit={max_text_only_retries}")
        if retry_bits:
            lines.append("Retry summary: " + ", ".join(retry_bits))

    placeholder_token = context.get("placeholder_token")
    if placeholder_token:
        lines.append(f"Placeholder detected in prompt: '{placeholder_token}'")

    requested_total = context.get("requested_total")
    if requested_total:
        lines.append(f"Requested variants: {requested_total}")

    size = context.get("size")
    if size:
        lines.append(f"Size: {size}")
    aspect_ratio = context.get("aspect_ratio")
    if aspect_ratio:
        lines.append(f"Aspect ratio: {aspect_ratio}")

    if exc.status is not None:
        lines.append(f"HTTP status: {exc.status}")

    request_id = context.get("request_id")
    if request_id:
        lines.append(f"OpenRouter request id: {request_id}")
    retry_after = context.get("retry_after")
    if retry_after:
        lines.append(f"Retry-After: {retry_after}")

    if exc.body:
        lines.append("Response snippet:")
        lines.append(_indent_block(exc.body))

    response_text_attempts = context.get("response_text_attempts")
    if isinstance(response_text_attempts, list) and response_text_attempts:
        lines.append("Provider text attempt breakdown:")
        for attempt in response_text_attempts:
            if not isinstance(attempt, dict):
                lines.append(f"  - {_clip_text(str(attempt), 200)}")
                continue
            attempt_id = attempt.get("attempt")
            attempt_reason = attempt.get("reason")
            attempt_detail = attempt.get("detail")
            line_bits = []
            if attempt_id is not None:
                line_bits.append(f"attempt {attempt_id}")
            if attempt_reason:
                line_bits.append(f"reason={attempt_reason}")
            if attempt_detail:
                line_bits.append(f"detail={_clip_text(str(attempt_detail), 200)}")
            header_line = "  - " + ", ".join(line_bits) if line_bits else "  -"
            lines.append(header_line)
            attempt_text = attempt.get("text")
            if isinstance(attempt_text, list):
                for idx, snippet in enumerate(attempt_text, start=1):
                    lines.append(f"      [{idx}] {_clip_text(str(snippet), 200)}")

    response_text = context.get("response_text")
    if isinstance(response_text, list) and response_text:
        lines.append("Provider text replies (flattened):")
        for idx, snippet in enumerate(response_text, start=1):
            lines.append(f"  [{idx}] {_clip_text(str(snippet), 200)}")

    if response_text_attempts or response_text:
        lines.append(
            "Action: confirm the prompt contains concrete visual directions (no TODO placeholders) before retrying."
        )

    consumed = {
        "campaign_id",
        "slot",
        "route_id",
        "placement_id",
        "variant_index",
        "reason",
        "model",
        "requested_total",
        "size",
        "aspect_ratio",
        "request_id",
        "retry_after",
        "response_text",
        "response_text_attempts",
        "attempts",
        "text_only_attempts",
        "max_text_only_retries",
        "placeholder_token",
    }
    extras = {
        key: value
        for key, value in context.items()
        if key not in consumed and value not in (None, "")
    }
    if extras:
        lines.append("Additional context:")
        for key, value in sorted(extras.items()):
            lines.append(f"  - {key}: {value}")

    lines.append(
        "Next steps: run `imgen provider openrouter status` to inspect API key usage, then see docs/playbooks/provider-errors.md#openrouter for remediation guidance."
    )
    lines.append(
        "Do not switch to legacy slot generation for campaign incidents—resolve the provider issue and rerun the campaign command instead."
    )
    return "\n".join(lines)


def _indent_block(text: str, indent: str = "  ") -> str:
    return "\n".join(f"{indent}{line}" if line else indent.rstrip() for line in text.splitlines())


def _clip_text(text: str, limit: int = 800) -> str:
    snippet = (text or "").strip()
    if len(snippet) <= limit:
        return snippet
    return snippet[: limit - 1] + "…"


def _detect_missing_provider_exception(exc: Exception) -> Optional[str]:
    message = str(exc)
    if isinstance(exc, NameError) and "ProviderExecutionError" in message:
        return (
            "This imgen CLI build is out of date and cannot surface provider errors. "
            "Upgrade to `imgen` >= 0.1.18 (pipx upgrade imgen-cli) and rerun the campaign command. "
            "Do not fall back to legacy slot generation for marketing flows; stop here and resolve the upgrade."
        )
    return None


class PromptPayload:
    def __init__(
        self,
        *,
        prompt: str,
        request_text: Optional[str],
        provider_options: Dict[str, Any],
        provider: Optional[str],
        model: Optional[str],
        generator: Optional[str],
        size: Optional[str],
        aspect_ratio: Optional[str],
        seed: Optional[int],
        count: Optional[int],
    ) -> None:
        self.prompt = prompt
        self.request_text = request_text
        self.provider_options = provider_options
        self.provider = provider
        self.model = model
        self.generator = generator
        self.size = size
        self.aspect_ratio = aspect_ratio
        self.seed = seed
        self.count = count


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 1
    return args.func(args)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
def _load_structured_data(path: str | Path) -> Dict[str, Any]:
    source: Path | None
    if path == "-":
        data = sys.stdin.read()
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            import yaml

            return yaml.safe_load(data) or {}
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"File not found: {source}")
    suffix = source.suffix.lower()
    if suffix in {".json"}:
        with source.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    if suffix in {".yaml", ".yml"}:
        import yaml

        with source.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    with source.open("r", encoding="utf-8") as fh:
        text = fh.read()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        import yaml

        return yaml.safe_load(text) or {}


def _read_text_payload(path: Optional[str]) -> Optional[str]:
    if not path:
        return None
    if path == "-":
        return sys.stdin.read()
    with Path(path).expanduser().open("r", encoding="utf-8") as fh:
        return fh.read()


def _split_csv(value: Optional[str]) -> Optional[list[str]]:
    if not value:
        return None
    items = [item.strip() for item in value.split(",") if item.strip()]
    return items or None


def _parse_metadata(pairs: Iterable[str]) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for item in pairs:
        if "=" not in item:
            raise ValueError(f"Metadata '{item}' must be in key=value format")
        key, value = item.split("=", 1)
        result[key.strip()] = value.strip()
    return result


def _sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()
