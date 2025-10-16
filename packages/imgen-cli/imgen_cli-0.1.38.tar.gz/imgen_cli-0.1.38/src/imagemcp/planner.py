from __future__ import annotations

import json
from dataclasses import asdict, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import quote_plus

from ._compat import dataclass
from .config import CONFIG_DIR_NAME, CONFIG_FILENAME, load_project_config
from .defaults import DEFAULT_GENERATOR, DEFAULT_PROVIDER, default_model_for_provider
from .storage import InvalidPathError, ProjectPaths, list_all_slots

DEFAULT_COUNT = 3


@dataclass()
class PlanConstraints:
    width: Optional[int] = None
    height: Optional[int] = None
    size: Optional[str] = None
    aspectRatio: Optional[str] = None
    seed: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    generator: Optional[str] = None
    providerOptions: Dict[str, object] = field(default_factory=dict)
    guidance: Optional[str] = None
    mood: Optional[str] = None
    palette: Optional[str] = None


@dataclass()
class PlanPayload:
    slot: str
    requestText: str
    constraints: PlanConstraints = field(default_factory=PlanConstraints)
    count: int = DEFAULT_COUNT
    provider: Optional[str] = None
    model: Optional[str] = None
    generator: Optional[str] = None
    projectRoot: Optional[str] = None


@dataclass()
class KnownContext:
    slot: Optional[str] = None
    constraints: Optional[PlanConstraints] = None
    projectRoot: Optional[str] = None


@dataclass()
class CollectContextPayload:
    requestText: Optional[str] = ""
    known: KnownContext = field(default_factory=KnownContext)


@dataclass()
class ProjectContextInfo:
    project_root: str
    project_id: Optional[str]
    target_root: Optional[str]
    gallery_url: Optional[str]
    known_slots: List[str]
    slot_exists: bool
    related_slots: List[str]
    warnings: List[str]


@dataclass()
class PlanInput:
    slot: str
    request_text: str
    constraints: Dict[str, object]
    count: int = DEFAULT_COUNT
    project_root: Optional[str] = None

    @classmethod
    def from_payload(cls, payload: PlanPayload) -> "PlanInput":
        constraints = _constraints_to_dict(payload.constraints)
        if payload.provider and "provider" not in constraints:
            constraints["provider"] = payload.provider
        if payload.model and "model" not in constraints:
            constraints["model"] = payload.model
        if payload.generator and "generator" not in constraints:
            constraints["generator"] = payload.generator
        return cls(
            slot=payload.slot,
            request_text=payload.requestText,
            constraints=constraints,
            count=payload.count or DEFAULT_COUNT,
            project_root=payload.projectRoot,
        )


def collect_context_questions(payload: CollectContextPayload) -> Dict[str, object]:
    known = payload.known or KnownContext()
    constraints = known.constraints
    missing = []
    if not known.slot:
        missing.append(
            {
                "field": "slot",
                "prompt": "Which slot should these variations update? (e.g. hero, testimonial-slot-1)",
                "type": "string",
            }
        )
    if constraints is None:
        missing.append(
            {
                "field": "constraints",
                "prompt": "Any size or aspect requirements? Provide width/height in px or aspect ratio (e.g. 16:9).",
                "type": "object",
            }
        )
    if not known.projectRoot:
        missing.append(
            {
                "field": "projectRoot",
                "prompt": "Absolute path to the project root (where .imagemcp/config.json lives).",
                "type": "string",
            }
        )
    defaults = {
        "count": DEFAULT_COUNT,
        "projectRoot": known.projectRoot or ".",
        "provider": DEFAULT_PROVIDER,
        "model": default_model_for_provider(DEFAULT_PROVIDER),
    }
    notes = [
        "Gather either an explicit size (e.g. 1024x1024) or an aspect ratio (e.g. 16:9); the planner will reject requests without geometry so the CLI receives clear instructions.",
        "The CLI promotes variant #0 immediately so previews update right away; other picks are available via the gallery server.",
        "Seeds are optional and provider-specific. Include one for reproducibility when the provider supports it.",
        "Image generation is locked to Gemini 2.5 (`{model}`); leave provider/model at their defaults.".format(
            model=default_model_for_provider(DEFAULT_PROVIDER)
        ),
    ]
    notes.extend(_geometry_hint_notes(constraints))
    if known.projectRoot:
        context = _resolve_project_context(
            known.slot or "",
            known.projectRoot,
            include_slot_warnings=False,
        )
        if context.known_slots:
            notes.append(
                "Known slots in this project: {slots}.".format(
                    slots=_format_slot_list(context.known_slots)
                )
            )
        if context.gallery_url:
            notes.append(
                "Gallery preview: {url}".format(url=context.gallery_url)
            )
        for warning in context.warnings:
            notes.append(warning)
    return {"missing": missing, "defaults": defaults, "notes": notes}


def plan_image_job(payload: PlanPayload) -> Dict[str, object]:
    plan_input = PlanInput.from_payload(payload)
    if not plan_input.slot:
        raise ValueError("'slot' is required")
    count = max(1, plan_input.count)
    size, aspect_ratio, warnings = _derive_geometry(plan_input.constraints)
    if size is None and aspect_ratio is None:
        raise ValueError("Provide either an explicit size or an aspect ratio before planning.")

    raw_provider = plan_input.constraints.get("provider")
    if raw_provider:
        provider = str(raw_provider)
        provider_explicit = True
    else:
        provider = DEFAULT_PROVIDER
        provider_explicit = False
    desired_model = default_model_for_provider(provider)
    model_notes: List[str] = []
    raw_model = plan_input.constraints.get("model")
    requested_model = str(raw_model) if raw_model else None
    if provider == "mock":
        model = requested_model or desired_model
        model_explicit = bool(requested_model)
    else:
        if requested_model and requested_model != desired_model:
            model_notes.append(
                "Requested model '{requested}' is not supported; locking to '{locked}' for stability.".format(
                    requested=requested_model,
                    locked=desired_model,
                )
            )
        model = desired_model
        model_explicit = True
        model_notes.append(
            "Gemini 2.5 ('{model}') is the only approved model; do not change provider/model in the CLI command.".format(
                model=model,
            )
        )
    plan_input.constraints["model"] = model
    raw_generator = plan_input.constraints.get("generator")
    if raw_generator:
        generator = str(raw_generator)
        generator_explicit = True
    elif provider == "mock":
        generator = "mock"
        generator_explicit = True
    else:
        generator = DEFAULT_GENERATOR
        generator_explicit = False
    seed = plan_input.constraints.get("seed")
    project_root_input = plan_input.project_root or "."
    project_context = _resolve_project_context(plan_input.slot, project_root_input)
    project_root = project_context.project_root
    init_note = (
        "If this is your first run, the CLI will auto-initialize the project at {project_root}."
    ).format(project_root=project_root)

    prompt = _build_prompt(plan_input.slot, plan_input.request_text, plan_input.constraints)
    stdin_payload = {
        "prompt": prompt,
        "requestText": plan_input.request_text,
        "providerOptions": plan_input.constraints.get("providerOptions", {}),
    }
    if provider_explicit:
        stdin_payload["provider"] = provider
    if model_explicit:
        stdin_payload["model"] = model
    if generator_explicit:
        stdin_payload["generator"] = generator
    if seed is not None:
        stdin_payload["seed"] = seed
    if size:
        stdin_payload["size"] = size
    if aspect_ratio:
        stdin_payload["aspectRatio"] = aspect_ratio
    notes = list(warnings)
    notes.extend(project_context.warnings)
    notes.extend(
        [
            init_note,
            "If the `imgen` command is missing or outdated, first install pipx (`brew install pipx`) and then run `pipx install imgen-cli` — never use `pip install` or `python -m pip`. See resource `setup://imgen-cli` for full instructions.",
            "Available provider/model combinations are documented in resource `setup://imgen-parameters`.",
        ]
    )
    if model_notes:
        notes.extend(model_notes)
    if project_context.gallery_url:
        notes.append(
            "After running the CLI, open the gallery at {url} to review and share variants.".format(
                url=project_context.gallery_url
            )
        )

    output: Dict[str, object] = {
        "plan": {
            "prompt": prompt,
            "n": count,
            "size": size,
            "aspectRatio": aspect_ratio,
            "seed": seed,
            "provider": provider,
            "model": model,
            "generator": generator,
            "providerOptions": plan_input.constraints.get("providerOptions", {}),
            "constraints": plan_input.constraints,
        },
        "cli": {
            "command": _build_cli_command(
                plan_input.slot,
                project_root,
                count,
                size,
                aspect_ratio,
                provider if provider_explicit else None,
                model if model_explicit else None,
                generator if generator_explicit or generator != DEFAULT_GENERATOR else None,
                prompt,
            ),
            "stdin": stdin_payload,
            "projectRoot": project_root,
            "requirements": {
                "command": "imgen",
                "minimumVersion": "0.1.0",
                "setupResource": "setup://imgen-cli",
                "installCommand": "pipx install imgen-cli",
                "upgradeCommand": "pipx upgrade imgen-cli",
                "pipxInstallCommand": "brew install pipx",
            },
        },
        "sessionHint": f"{plan_input.slot}-{datetime.utcnow().strftime('%Y%m%d')}",
        "costEstimate": {
            "unit": "image-variant",
            "quantity": count,
            "estimatedCredits": count * 1.0,
        },
        "notes": notes,
    }
    slot_payload: Dict[str, object] = {
        "requested": plan_input.slot,
        "exists": project_context.slot_exists,
    }
    if project_context.related_slots:
        slot_payload["related"] = project_context.related_slots
        slot_payload["recommended"] = project_context.related_slots[0]
    output["slot"] = slot_payload

    project_payload: Dict[str, object] = {"projectRoot": project_root}
    if project_context.project_id:
        project_payload["projectId"] = project_context.project_id
    if project_context.target_root:
        project_payload["targetRoot"] = project_context.target_root
    if project_context.gallery_url:
        project_payload["galleryUrl"] = project_context.gallery_url
    if project_context.known_slots:
        project_payload["knownSlots"] = project_context.known_slots
    output["project"] = project_payload

    return output


def _resolve_project_context(
    slot: str,
    project_root: str,
    *,
    include_slot_warnings: bool = True,
) -> ProjectContextInfo:
    root_path = Path(project_root).expanduser()
    # Avoid resolving non-existent paths to keep remote usage flexible.
    normalized_root = root_path.resolve(strict=False)
    config_path = normalized_root / CONFIG_DIR_NAME / CONFIG_FILENAME
    known_slots: List[str] = []
    warnings: List[str] = []
    project_id: Optional[str] = None
    target_root: Optional[str] = None
    gallery_url: Optional[str] = None

    if config_path.exists():
        try:
            config = load_project_config(normalized_root)
        except FileNotFoundError:
            warnings.append(
                f"Project config not found at {config_path} despite existence check; re-run `imgen init`."
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            warnings.append(
                f"Unable to load project config at {config_path}: {exc!s}."
            )
        else:
            project_id = config.project_id
            target_root = config.target_root
            gallery_url = _build_gallery_url(config, slot)
            try:
                paths = ProjectPaths.create(normalized_root, Path(config.target_root))
            except (InvalidPathError, ValueError) as exc:
                warnings.append(f"Invalid target root '{config.target_root}': {exc!s}.")
            else:
                grouped = list_all_slots(paths)
                known_slots = sorted(grouped.keys())
                if not known_slots and not paths.sessions_root.exists():
                    warnings.append(
                        "No prior sessions found; the CLI will create the slot on first generation."
                    )
    else:
        # Provide a gentle hint when the config is missing entirely.
        warnings.append(
            f"Project root {normalized_root} is missing {CONFIG_DIR_NAME}/{CONFIG_FILENAME}; run `imgen init` first."
        )

    slot_exists = slot in known_slots
    related_slots = _related_slots(slot, known_slots) if known_slots else []
    if include_slot_warnings:
        if not slot_exists and related_slots:
            preview = _format_slot_list(related_slots)
            warnings.append(
                f"Slot '{slot}' is new; similar existing slots include: {preview}. Consider reusing one of them to avoid duplicates."
            )
        elif not slot_exists and known_slots:
            preview = _format_slot_list(known_slots)
            warnings.append(
                f"Slot '{slot}' is new for this project. Known slots: {preview}."
            )

    return ProjectContextInfo(
        project_root=str(normalized_root),
        project_id=project_id,
        target_root=target_root,
        gallery_url=gallery_url,
        known_slots=known_slots,
        slot_exists=slot_exists,
        related_slots=related_slots,
        warnings=warnings,
    )


def _derive_geometry(constraints: Dict[str, object]) -> tuple[Optional[str], Optional[str], List[str]]:
    size: Optional[str] = None
    aspect_ratio: Optional[str] = None
    warnings: List[str] = []
    explicit_size = constraints.get("size")
    width = constraints.get("width")
    height = constraints.get("height")
    aspect = constraints.get("aspectRatio")

    if explicit_size:
        size = str(explicit_size)
    elif width is not None or height is not None:
        if width is None or height is None:
            warnings.append("Both width and height are required to form an explicit size.")
        else:
            try:
                size = f"{int(width)}x{int(height)}"
            except (TypeError, ValueError):
                warnings.append("Width/height constraints must be integers; omit or correct them before planning.")
    if size is None and aspect:
        aspect_ratio = str(aspect)
    if size and aspect:
        warnings.append("Both explicit size and aspect provided; using explicit size per policy.")
    if size is None and aspect_ratio is None:
        warnings.append("No geometry provided; supply size or aspect ratio to control generation.")
    return size, aspect_ratio, warnings


def _build_gallery_url(config, slot: str) -> str:
    project_param = quote_plus(config.project_id)
    slot_param = quote_plus(slot)
    host = getattr(config, "gallery_host", "localhost")
    port = getattr(config, "gallery_port", 8765)
    return f"http://{host}:{port}/?project={project_param}&slot={slot_param}"


def _related_slots(slot: str, known_slots: List[str]) -> List[str]:
    slot_lower = slot.lower()
    related: List[str] = []
    for candidate in known_slots:
        candidate_lower = candidate.lower()
        if candidate_lower == slot_lower:
            related.append(candidate)
        elif candidate_lower in slot_lower or slot_lower in candidate_lower:
            related.append(candidate)
    if related:
        return sorted(dict.fromkeys(related))
    # Fall back to a simple prefix match on hyphenated segments.
    base = slot_lower.split("-")[0]
    secondary = [c for c in known_slots if c.lower().startswith(base) and c not in related]
    related.extend(secondary)
    return sorted(dict.fromkeys(related))


def _format_slot_list(slots: List[str], limit: int = 5) -> str:
    if not slots:
        return ""
    if len(slots) <= limit:
        return ", ".join(slots)
    shown = ", ".join(slots[:limit])
    remaining = len(slots) - limit
    return f"{shown}, … (+{remaining} more)"


def _constraints_to_dict(constraints: PlanConstraints) -> Dict[str, object]:
    data = asdict(constraints)
    return {k: v for k, v in data.items() if v not in (None, {}, [])}


def _geometry_hint_notes(constraints: Optional[PlanConstraints]) -> List[str]:
    if not constraints:
        return []
    notes: List[str] = []
    if constraints.width and constraints.height:
        notes.append(f"Known geometry: {constraints.width}x{constraints.height} pixels.")
    elif constraints.aspectRatio:
        notes.append(f"Known aspect ratio: {constraints.aspectRatio}.")
    return notes


def normalize_plan_payload(payload: PlanPayload | Dict[str, object] | str) -> PlanPayload:
    if isinstance(payload, PlanPayload):
        return payload
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Payload must be a JSON object.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object.")
    constraints_data = payload.get("constraints") or {}
    if isinstance(constraints_data, str):
        constraints_data = json.loads(constraints_data)
    constraints = PlanConstraints(**constraints_data)
    count_raw = payload.get("count", DEFAULT_COUNT)
    try:
        count_value = int(count_raw)
    except (TypeError, ValueError):
        count_value = DEFAULT_COUNT
    project_root_raw = payload.get("projectRoot")
    project_root = str(project_root_raw) if project_root_raw is not None else None
    return PlanPayload(
        slot=str(payload.get("slot", "")),
        requestText=str(payload.get("requestText", "")),
        constraints=constraints,
        count=count_value,
        provider=payload.get("provider"),
        model=payload.get("model"),
        generator=payload.get("generator"),
        projectRoot=project_root,
    )


def normalize_collect_context_payload(
    payload: CollectContextPayload | Dict[str, object] | str,
) -> CollectContextPayload:
    if isinstance(payload, CollectContextPayload):
        return payload
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValueError("Payload must be a JSON object.") from exc
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON object.")
    known_data = payload.get("known") or {}
    if isinstance(known_data, str):
        known_data = json.loads(known_data)
    constraints_data = known_data.get("constraints") or {}
    if isinstance(constraints_data, str):
        constraints_data = json.loads(constraints_data)
    known_project_root_raw = known_data.get("projectRoot")
    known_project_root = (
        str(known_project_root_raw) if known_project_root_raw is not None else None
    )
    known = KnownContext(
        slot=known_data.get("slot"),
        constraints=PlanConstraints(**constraints_data) if constraints_data else None,
        projectRoot=known_project_root,
    )
    request_text_raw = payload.get("requestText")
    request_text = str(request_text_raw) if request_text_raw is not None else None
    return CollectContextPayload(
        requestText=request_text,
        known=known,
    )


__all__ = [
    "CollectContextPayload",
    "PlanConstraints",
    "PlanPayload",
    "collect_context_questions",
    "plan_image_job",
    "normalize_plan_payload",
    "normalize_collect_context_payload",
]


def _build_prompt(slot: str, request_text: str, constraints: Dict[str, object]) -> str:
    guidance = constraints.get("guidance")
    description = request_text or f"Generate {DEFAULT_COUNT} fresh variants"
    base = description.strip()
    pieces = [base, f"Slot: {slot}"]
    if guidance:
        pieces.append(f"Guidance: {guidance}")
    mood = constraints.get("mood")
    if mood:
        pieces.append(f"Mood: {mood}")
    palette = constraints.get("palette")
    if palette:
        pieces.append(f"Palette: {palette}")
    return " | ".join(pieces)


def _build_cli_command(
    slot: str,
    project_root: Optional[str],
    count: int,
    size: Optional[str],
    aspect_ratio: Optional[str],
    provider: Optional[str],
    model: Optional[str],
    generator: Optional[str],
    prompt: str,
) -> List[str]:
    command: List[str] = ["imgen"]
    if project_root and project_root != ".":
        command.extend(["--project-root", str(project_root)])
    command.extend([
        "gen",
        "--slot",
        slot,
        "--n",
        str(count),
        "--prompt",
        prompt,
        "--json",
    ])
    if provider:
        command.extend(["--provider", provider])
    if model:
        command.extend(["--model", model])
    if generator:
        command.extend(["--generator", generator])
    if size:
        command.extend(["--size", size])
    elif aspect_ratio:
        command.extend(["--aspect-ratio", aspect_ratio])
    return command


__all__ = ["collect_context_questions", "plan_image_job"]
from ._compat import dataclass
