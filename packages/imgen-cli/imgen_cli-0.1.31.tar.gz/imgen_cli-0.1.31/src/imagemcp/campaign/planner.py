"""Campaign planning helpers for FastMCP integration.

This module mirrors the slot planner utilities in ``imagemcp.planner`` but
focuses on the campaign workflow. It provides lightweight dataclasses so the
FastMCP server can accept loosely typed JSON payloads, normalize them, and
return deterministic CLI plans for agents such as Claude Code. The goal is to
keep the remote planner stateless: it emits structured steps and leaves file
system mutations to the local ``imgen`` CLI orchestrator.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from ..defaults import DEFAULT_GENERATOR, DEFAULT_PROVIDER, default_model_for_provider
from ..templates_catalog import load_default_placement_templates

# ---------------------------------------------------------------------------
# Payload dataclasses (normalized from JSON/dicts)
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class CampaignBriefDraft:
    """Incoming brief details collected from the user or agent."""

    campaign_id: Optional[str] = None
    name: Optional[str] = None
    objective: Optional[str] = None
    tagline: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    placements: List[str] = field(default_factory=list)
    routes: List[str] = field(default_factory=list)
    generator: Optional[str] = None
    provider: Optional[str] = None
    variants: Optional[int] = None


@dataclass(slots=True)
class CollectCampaignBriefPayload:
    """Payload for ``collect_campaign_brief``."""

    brief: CampaignBriefDraft = field(default_factory=CampaignBriefDraft)
    projectRoot: Optional[str] = None


@dataclass(slots=True)
class RoutePlanInput:
    """Route definition provided to ``plan_campaign_routes``."""

    route_id: str
    name: Optional[str] = None
    summary: Optional[str] = None
    prompt_template: Optional[str] = None
    prompt_tokens: List[str] = field(default_factory=list)
    copy_tokens: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    source: Optional[str] = None


@dataclass(slots=True)
class PlacementPlanInput:
    """Placement definition provided to ``plan_campaign_routes``."""

    placement_id: str
    template_id: Optional[str] = None
    variants: Optional[int] = None
    provider: Optional[str] = None
    copy_tokens: List[str] = field(default_factory=list)
    notes: Optional[str] = None


@dataclass(slots=True)
class PlanCampaignRoutesPayload:
    """Payload describing a campaign generation request."""

    campaign_id: str
    name: Optional[str] = None
    objective: Optional[str] = None
    routes: List[RoutePlanInput] = field(default_factory=list)
    placements: List[PlacementPlanInput] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    generator: Optional[str] = None
    provider: Optional[str] = None
    variants: Optional[int] = None
    summary_only: bool = True
    export_platform: Optional[str] = None
    include_states: List[str] = field(default_factory=lambda: ["approved"])
    projectRoot: Optional[str] = None


@dataclass(slots=True)
class PlanBatchGenerationPayload:
    """Payload describing a deterministic batch workflow."""

    campaign_id: str
    routes: List[str] = field(default_factory=list)
    placements: List[str] = field(default_factory=list)
    variants: Optional[int] = None
    provider: Optional[str] = None
    generator: Optional[str] = None
    summary_only: bool = True
    export_platform: Optional[str] = None
    include_states: List[str] = field(default_factory=lambda: ["approved"])
    batch_filename: str = "batch.yaml"
    projectRoot: Optional[str] = None


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def normalize_collect_campaign_brief_payload(
    payload: CollectCampaignBriefPayload | dict[str, object] | str,
) -> CollectCampaignBriefPayload:
    """Accept JSON/string/dict payloads and produce a dataclass instance."""

    if isinstance(payload, CollectCampaignBriefPayload):
        return payload
    data = _coerce_to_dict(payload)
    brief_payload = data.get("brief", {})
    if not isinstance(brief_payload, dict):  # pragma: no cover - defensive
        raise TypeError("'brief' must be a mapping when collecting campaign brief")
    brief = CampaignBriefDraft(
        campaign_id=_optional_str(brief_payload.get("campaign_id")),
        name=_optional_str(brief_payload.get("name")),
        objective=_optional_str(brief_payload.get("objective")),
        tagline=_optional_str(brief_payload.get("tagline")),
        tags=_string_list(brief_payload.get("tags")),
        placements=_string_list(brief_payload.get("placements")),
        routes=_string_list(brief_payload.get("routes")),
        generator=_optional_str(brief_payload.get("generator")),
        provider=_optional_str(brief_payload.get("provider")),
        variants=_optional_int(brief_payload.get("variants")),
    )
    project_root = _optional_str(data.get("projectRoot"))
    return CollectCampaignBriefPayload(brief=brief, projectRoot=project_root)


def normalize_plan_campaign_routes_payload(
    payload: PlanCampaignRoutesPayload | dict[str, object] | str,
) -> PlanCampaignRoutesPayload:
    """Normalize incoming plan requests for campaign generation."""

    if isinstance(payload, PlanCampaignRoutesPayload):
        return payload
    data = _coerce_to_dict(payload)
    campaign_id = _optional_str(data.get("campaign_id"))
    if not campaign_id:
        raise ValueError("'campaign_id' is required for plan_campaign_routes")

    route_payloads = data.get("routes", [])
    if not isinstance(route_payloads, Iterable):
        raise TypeError("'routes' must be a list")
    routes: List[RoutePlanInput] = []
    for raw in route_payloads:
        if isinstance(raw, str):
            raw = {"route_id": raw}
        elif not isinstance(raw, dict):
            raise TypeError("route entries must be mappings or strings")
        route_id = _optional_str(raw.get("route_id"))
        if not route_id:
            raise ValueError("Each route requires a 'route_id'")
        routes.append(
            RoutePlanInput(
                route_id=route_id,
                name=_optional_str(raw.get("name")),
                summary=_optional_str(raw.get("summary")),
                prompt_template=_optional_str(raw.get("prompt_template")),
                prompt_tokens=_string_list(raw.get("prompt_tokens")),
                copy_tokens=_string_list(raw.get("copy_tokens")),
                notes=_optional_str(raw.get("notes")),
                source=_optional_str(raw.get("source")),
            )
        )

    placement_payloads = data.get("placements", [])
    if not isinstance(placement_payloads, Iterable):
        raise TypeError("'placements' must be a list")
    placements: List[PlacementPlanInput] = []
    for raw in placement_payloads:
        if isinstance(raw, str):
            raw = {"placement_id": raw}
        elif not isinstance(raw, dict):
            raise TypeError("placement entries must be mappings or strings")
        placement_id = _optional_str(raw.get("placement_id"))
        if not placement_id:
            raise ValueError("Each placement requires a 'placement_id'")
        placements.append(
            PlacementPlanInput(
                placement_id=placement_id,
                template_id=_optional_str(raw.get("template_id")),
                variants=_optional_int(raw.get("variants")),
                provider=_optional_str(raw.get("provider")),
                copy_tokens=_string_list(raw.get("copy_tokens")),
                notes=_optional_str(raw.get("notes")),
            )
        )

    include_states = data.get("include_states", ["approved"])
    if not isinstance(include_states, Iterable):
        raise TypeError("'include_states' must be a list")

    return PlanCampaignRoutesPayload(
        campaign_id=campaign_id,
        name=_optional_str(data.get("name")),
        objective=_optional_str(data.get("objective")),
        routes=routes,
        placements=placements,
        tags=_string_list(data.get("tags")),
        generator=_optional_str(data.get("generator")),
        provider=_optional_str(data.get("provider")),
        variants=_optional_int(data.get("variants")),
        summary_only=bool(data.get("summary_only", True)),
        export_platform=_optional_str(data.get("export_platform")),
        include_states=[str(state) for state in include_states if state],
        projectRoot=_optional_str(data.get("projectRoot")),
    )


def normalize_plan_batch_generation_payload(
    payload: PlanBatchGenerationPayload | dict[str, object] | str,
) -> PlanBatchGenerationPayload:
    """Normalize incoming batch workflow requests."""

    if isinstance(payload, PlanBatchGenerationPayload):
        return payload
    data = _coerce_to_dict(payload)
    campaign_id = _optional_str(data.get("campaign_id"))
    if not campaign_id:
        raise ValueError("'campaign_id' is required for plan_batch_generation")
    include_states = data.get("include_states", ["approved"])
    if not isinstance(include_states, Iterable):
        raise TypeError("'include_states' must be a list")
    return PlanBatchGenerationPayload(
        campaign_id=campaign_id,
        routes=_string_list(data.get("routes")),
        placements=_string_list(data.get("placements")),
        variants=_optional_int(data.get("variants")),
        provider=_optional_str(data.get("provider")),
        generator=_optional_str(data.get("generator")),
        summary_only=bool(data.get("summary_only", True)),
        export_platform=_optional_str(data.get("export_platform")),
        include_states=[str(state) for state in include_states if state],
        batch_filename=_optional_str(data.get("batch_filename")) or "batch.yaml",
        projectRoot=_optional_str(data.get("projectRoot")),
    )


# ---------------------------------------------------------------------------
# Planner primitives
# ---------------------------------------------------------------------------


def collect_campaign_brief(payload: CollectCampaignBriefPayload) -> Dict[str, object]:
    """Return missing questions, defaults, and catalog hints for a campaign brief."""

    brief = payload.brief
    missing: List[Dict[str, object]] = []
    if not brief.campaign_id:
        missing.append(
            {
                "field": "campaign_id",
                "prompt": "Campaign slug (e.g., spring_wave). Use lowercase with hyphens/underscores.",
                "type": "string",
            }
        )
    if not brief.name:
        missing.append(
            {
                "field": "name",
                "prompt": "Human-friendly campaign name for reports and exports.",
                "type": "string",
            }
        )
    if not brief.objective:
        missing.append(
            {
                "field": "objective",
                "prompt": "What is the primary marketing objective or message?",
                "type": "string",
            }
        )
    if not brief.routes:
        missing.append(
            {
                "field": "routes",
                "prompt": "List at least one creative route (e.g., ocean_luxury, capsule_wardrobe).",
                "type": "list",
            }
        )
    if not brief.placements:
        missing.append(
            {
                "field": "placements",
                "prompt": "Select placements from the catalog (e.g., meta_feed_square, meta_story_vertical).",
                "type": "list",
            }
        )

    effective_generator = brief.generator or DEFAULT_GENERATOR
    defaults: Dict[str, object] = {
        "generator": effective_generator,
        "provider": brief.provider or ("mock" if effective_generator == "mock" else DEFAULT_PROVIDER),
        "variants": brief.variants or 2,
        "tags": brief.tags or (["mock"] if effective_generator == "mock" else []),
    }
    if payload.projectRoot:
        defaults["projectRoot"] = payload.projectRoot

    catalog = _summarize_placement_catalog(limit=8)
    notes = [
        "Campaign planner is stateless; all files stay local when you run the `imgen` CLI.",
        "Use `imgen campaign templates list` for the full placement catalog after initialization.",
        "Run `imgen campaign init <campaign_id>` once the brief is ready, then add routes and placements.",
        "Check progress with `imgen campaign status <campaign_id>` (or the FastMCP campaign_status_tool) whenever you resume work.",
        "Marketing work must stay on the campaign pipeline—do not fall back to slot tooling for missing variants.",
    ]
    if brief.generator == "mock" or DEFAULT_GENERATOR == "mock":
        notes.append("Mock generator keeps runs offline; switch generator/provider if you need hosted models.")

    return {
        "missing": missing,
        "defaults": defaults,
        "notes": notes,
        "catalog": {
            "placements": catalog,
        },
    }


def plan_campaign_routes(payload: PlanCampaignRoutesPayload) -> Dict[str, object]:
    """Produce CLI steps for initializing a campaign and generating variants."""

    if not payload.routes:
        raise ValueError("Provide at least one route for plan_campaign_routes")
    if not payload.placements:
        raise ValueError("Provide at least one placement for plan_campaign_routes")

    project_root = _normalize_project_root(payload.projectRoot)
    generator = payload.generator or DEFAULT_GENERATOR
    provider = payload.provider or ("mock" if generator == "mock" else DEFAULT_PROVIDER)
    model = default_model_for_provider(provider)
    variants = payload.variants or max((item.variants or 2) for item in payload.placements)
    routes_csv = ",".join(route.route_id for route in payload.routes)
    placements_csv = ",".join(item.placement_id for item in payload.placements)
    include_states = payload.include_states or ["approved"]
    export_platform = payload.export_platform or _default_export_platform(payload.placements)

    actions: List[Dict[str, object]] = []
    init_cmd = ["imgen", "campaign", "init", payload.campaign_id]
    if payload.name:
        init_cmd.extend(["--name", payload.name])
    if payload.objective:
        init_cmd.extend(["--objective", payload.objective])
    if payload.tags:
        init_cmd.extend(["--tags", ",".join(payload.tags)])
    actions.append(
        _action(
            step="init",
            description=f"Initialize campaign {payload.campaign_id}",
            command=init_cmd,
        )
    )

    for route in payload.routes:
        cmd = [
            "imgen",
            "campaign",
            "route",
            "add",
            payload.campaign_id,
            route.route_id,
        ]
        if route.name:
            cmd.extend(["--name", route.name])
        if route.summary:
            cmd.extend(["--summary", route.summary])
        if route.source:
            cmd.extend(["--source", route.source])
        if route.prompt_template:
            cmd.extend(["--prompt-template", route.prompt_template])
        for token in route.prompt_tokens:
            cmd.extend(["--prompt", token])
        for token in route.copy_tokens:
            cmd.extend(["--copy", token])
        if route.notes:
            cmd.extend(["--notes", route.notes])
        actions.append(
            _action(
                step=f"route:{route.route_id}",
                description=f"Ensure route {route.route_id} exists",
                command=cmd,
            )
        )

    for placement in payload.placements:
        cmd = [
            "imgen",
            "campaign",
            "placement",
            "add",
            payload.campaign_id,
            placement.placement_id,
        ]
        if placement.template_id:
            cmd.extend(["--template", placement.template_id])
        if placement.variants:
            cmd.extend(["--variants", str(placement.variants)])
        if placement.provider:
            cmd.extend(["--provider", placement.provider])
        for token in placement.copy_tokens:
            cmd.extend(["--copy", token])
        if placement.notes:
            cmd.extend(["--notes", placement.notes])
        actions.append(
            _action(
                step=f"placement:{placement.placement_id}",
                description=f"Add placement {placement.placement_id}",
                command=cmd,
            )
        )

    generate_cmd = [
        "imgen",
        "campaign",
        "generate",
        payload.campaign_id,
        "--routes",
        routes_csv,
        "--placements",
        placements_csv,
        "--variants",
        str(variants),
    ]
    if generator:
        generate_cmd.extend(["--generator", generator])
    if provider and provider != "mock":
        generate_cmd.extend(["--provider", provider])
    if payload.summary_only:
        generate_cmd.append("--summary-only")
    actions.append(
        _action(
            step="generate",
            description="Run campaign generation",
            command=generate_cmd,
        )
    )

    status_cmd = [
        "imgen",
        "campaign",
        "status",
        payload.campaign_id,
        "--json",
    ]
    actions.append(
        _action(
            step="status",
            description="Summarize campaign state (useful for resume & QA)",
            command=status_cmd,
        )
    )

    export_cmd = [
        "imgen",
        "campaign",
        "export",
        payload.campaign_id,
        "--platform",
        export_platform,
        "--include",
        ",".join(include_states),
    ]
    if payload.summary_only:
        export_cmd.append("--summary-only")
    actions.append(
        _action(
            step="export",
            description=f"Export approved assets for {export_platform}",
            command=export_cmd,
        )
    )

    plan_summary = {
        "campaign_id": payload.campaign_id,
        "name": payload.name,
        "objective": payload.objective,
        "routes": [asdict(route) for route in payload.routes],
        "placements": [asdict(place) for place in payload.placements],
        "generator": generator,
        "provider": provider,
        "model": model,
        "variants": variants,
        "export_platform": export_platform,
        "include_states": include_states,
    }

    notes = [
        "Ensure the CLI is installed (pipx install imgen-cli) before executing the plan (imgen >= 0.1.18).",
        "Routes and placements are idempotent; rerunning the same commands updates existing files.",
        "Use `imgen campaign status <id>` or the `campaign_status_tool` to inspect progress before/after generation and resume safely.",
        "Generation uses the summary-only flag so logs stay concise; drop it if you need detailed output.",
        "If a generate step fails, rerun the campaign command after fixing the issue—do not switch to slot-based `imgen gen` for marketing creatives.",
    ]

    return {
        "plan": plan_summary,
        "cli": {
            "projectRoot": project_root,
            "actions": actions,
            "requirements": _cli_requirements(),
        },
        "notes": notes,
    }


def plan_batch_generation(payload: PlanBatchGenerationPayload) -> Dict[str, object]:
    """Produce CLI steps for scaffolding and executing a deterministic batch run."""

    project_root = _normalize_project_root(payload.projectRoot)
    generator = payload.generator or DEFAULT_GENERATOR
    provider = payload.provider or ("mock" if generator == "mock" else DEFAULT_PROVIDER)
    export_platform = payload.export_platform or "meta_ads"
    include_states = payload.include_states or ["approved"]

    scaffold_cmd = [
        "imgen",
        "campaign",
        "batch-scaffold",
        payload.campaign_id,
        "--output",
        payload.batch_filename,
    ]
    if payload.routes:
        scaffold_cmd.extend(["--routes", ",".join(payload.routes)])
    if payload.placements:
        scaffold_cmd.extend(["--placements", ",".join(payload.placements)])
    if payload.variants:
        scaffold_cmd.extend(["--variants", str(payload.variants)])
    if provider and provider != "mock":
        scaffold_cmd.extend(["--provider", provider])

    batch_cmd = [
        "imgen",
        "campaign",
        "batch",
        payload.campaign_id,
        "--spec",
        payload.batch_filename,
    ]
    if generator:
        batch_cmd.extend(["--generator", generator])
    if payload.summary_only:
        batch_cmd.append("--summary-only")

    status_cmd = [
        "imgen",
        "campaign",
        "status",
        payload.campaign_id,
        "--json",
    ]

    export_cmd = [
        "imgen",
        "campaign",
        "export",
        payload.campaign_id,
        "--platform",
        export_platform,
        "--include",
        ",".join(include_states),
    ]
    if payload.summary_only:
        export_cmd.append("--summary-only")

    actions = [
        _action(
            step="batch-scaffold",
            description=f"Scaffold batch spec to {payload.batch_filename}",
            command=scaffold_cmd,
        ),
        _action(
            step="batch",
            description="Run deterministic batch",
            command=batch_cmd,
        ),
        _action(
            step="status",
            description="Summarize campaign state (useful for resume & QA)",
            command=status_cmd,
        ),
        _action(
            step="export",
            description=f"Export approved assets for {export_platform}",
            command=export_cmd,
        ),
    ]

    notes = [
        "Batch scaffold regenerates the spec each time; commit the file if you need CI reproducibility.",
        "Batch command streams JSONL logs into .imagemcp/campaigns/<id>/logs; attach them to debugging reports.",
        "Use `imgen campaign status <id>` or the `campaign_status_tool` between runs to confirm outstanding variants before resuming.",
        "Keep campaign remediation inside the campaign CLI—never fall back to legacy slot commands for missing marketing assets.",
    ]

    return {
        "plan": {
            "campaign_id": payload.campaign_id,
            "routes": payload.routes,
            "placements": payload.placements,
            "batch_filename": payload.batch_filename,
            "generator": generator,
            "provider": provider,
            "export_platform": export_platform,
            "include_states": include_states,
        },
        "cli": {
            "projectRoot": project_root,
            "actions": actions,
            "requirements": _cli_requirements(),
        },
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cli_requirements() -> Dict[str, object]:
    return {
        "command": "imgen",
        "minimumVersion": "0.1.18",
        "setupResource": "setup://imgen-cli",
        "installCommand": "pipx install imgen-cli",
        "upgradeCommand": "pipx upgrade imgen-cli",
        "pipxInstallCommand": "brew install pipx",
    }


def _coerce_to_dict(payload: dict[str, object] | str | CollectCampaignBriefPayload | PlanCampaignRoutesPayload | PlanBatchGenerationPayload) -> dict[str, object]:
    if isinstance(payload, str):
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError("String payload must be JSON") from exc
        if not isinstance(data, dict):
            raise TypeError("JSON payload must decode to an object")
        return data
    if isinstance(payload, dict):
        return payload
    raise TypeError("Unsupported payload type; call the normalize_* helper first")


def _optional_str(value: object) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return str(value)


def _optional_int(value: object) -> Optional[int]:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _string_list(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable):
        result: List[str] = []
        for item in value:
            if item is None:
                continue
            result.append(str(item).strip())
        return [item for item in result if item]
    raise TypeError("Expected string or iterable for list payload")


def _action(step: str, description: str, command: List[str]) -> Dict[str, object]:
    return {
        "step": step,
        "description": description,
        "command": command,
    }


def _summarize_placement_catalog(limit: int) -> List[Dict[str, object]]:
    templates = load_default_placement_templates()
    summary: List[Dict[str, object]] = []
    for template in templates[:limit]:
        summary.append(
            {
                "template_id": template.get("template_id"),
                "platform": template.get("platform"),
                "format": template.get("format"),
                "aspect_ratio": template.get("aspect_ratio"),
                "min_variants": template.get("min_variants"),
            }
        )
    return summary


def _normalize_project_root(project_root: Optional[str]) -> str:
    if not project_root:
        return str(Path.cwd())
    return str(Path(project_root).expanduser().resolve(strict=False))


def _default_export_platform(placements: Iterable[PlacementPlanInput]) -> str:
    for placement in placements:
        if placement.template_id and placement.template_id.startswith("meta_"):
            return "meta_ads"
        if placement.placement_id.startswith("meta_"):
            return "meta_ads"
    return "meta_ads"


__all__ = [
    "CampaignBriefDraft",
    "CollectCampaignBriefPayload",
    "RoutePlanInput",
    "PlacementPlanInput",
    "PlanCampaignRoutesPayload",
    "PlanBatchGenerationPayload",
    "normalize_collect_campaign_brief_payload",
    "normalize_plan_campaign_routes_payload",
    "normalize_plan_batch_generation_payload",
    "collect_campaign_brief",
    "plan_campaign_routes",
    "plan_batch_generation",
]
