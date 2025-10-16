# Image Slots Toolkit

This repository provides a complete workflow for managing durable image slots with generated variants. It includes:

- A remote FastMCP planner (`server.py`) that helps agents gather missing context and build CLI commands without touching local paths.
- A local CLI executor (`imgen`) that generates variants via the OpenRouter HTTP API (defaulting to Google Gemini 2.5 Flash Image Preview), writes session manifests, promotes variants atomically, and surfaces structured JSON for agents.
- A campaign workspace engine (`imgen campaign …`) that turns structured briefs into route/placement folders, deterministic manifests, thumbnails, batch logs, and ready-to-upload exports.
- A lightweight gallery server (`imgen gallery serve`) for browsing sessions and switching variants from the browser (campaign browsing coming soon).

## Getting started

1. Create a virtual environment and install dependencies from the lockfile:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
   ```

2. Install the package in editable mode if you want the `imgen` console script locally:

   ```bash
   uv pip install -e .
   ```

   (Once published to PyPI you can install globally via `pipx install imgen-cli`.)

3. Confirm the CLI is available:

```bash
imgen --help
```

## Project setup

Initialize a project once to create `.imagemcp/config.json` and register the target asset directory:

```bash
imgen init \
  --project-root /path/to/your/project \
  --target-root public/img
```

After this step, all CLI commands auto-detect the project root (even when called from subdirectories) and write assets under the configured target folder.

## CLI usage

Generate variants for a slot and receive structured JSON:

```bash
imgen gen \
  --slot hero \
  --target-root public/img \
  --prompt "Launch hero concept" \
  --n 3 \
  --json
```

- Variants are written under `.imagemcp/.sessions/<slot>_<sessionId>/` with a manifest (`session.json`).
- The first variant is auto-promoted to `<targetRoot>/<slot>.png` using atomic writes.
- CLI output includes the selected index, target path, session directory, warnings, and a localhost gallery URL.

Switch to a different variant later:

```bash
imgen select \
  --target-root public/img \
  --slot hero \
  --session hero-20250101_abcdef \
  --index 2 \
  --json
```

Inspect slots and sessions:

```bash
imgen slots list --target-root public/img
imgen sessions list --target-root public/img --slot hero
imgen sessions info --target-root public/img --slot hero --session hero-20250101_abcdef
```

## Campaign workflows (MVP)

Campaign mode lives alongside the existing slot tooling. Each campaign is stored under `.imagemcp/campaigns/<campaign_id>/` with subdirectories for routes, placements, thumbnails, exports, and logs. Commands enforce deterministic seeds and only accept providers certified for reproducible output (currently `openrouter:gemini-2.5-flash-image-preview` and the local `mock` generator).

List the bundled placement templates at any time:

```bash
imgen templates list --platform meta
```

### Initialize a campaign

```bash
imgen campaign init spring_wave \
  --name "Spring Wave Launch" \
  --objective "Drive awareness for Spring Wave collection" \
  --placements meta_square_awareness,meta_story_vertical \
  --tags awareness,new_customer
```

This scaffolds `.imagemcp/campaigns/spring_wave/` with a `campaign.yaml` brief and empty `routes/`, `placements/`, `thumbnails/`, `exports/`, and `logs/` directories. You can seed additional metadata by passing `--brief-file` (YAML/JSON) or `--metadata key=value` pairs for supporting assets.

Add routes via the CLI—no manual YAML required:

```bash
imgen campaign route add spring_wave ocean_luxury \
  --summary "Spotlight oceanfront suites with relaxed premium vibes." \
  --prompt-template "Stylized coastal resort hero shot at sunset with subtle copy {{copy.headline}}." \
  --prompt "cinematic lighting" \
  --prompt "editorial photography" \
  --copy "Oceanfront suites"
```

Repeat for additional routes (or load templates from a file with `--input`). Use `imgen campaign placement add` when you need to override `campaign.yaml` placements after initialization.

Inspect or curate campaign metadata without touching the filesystem:

```bash
imgen campaign route list spring_wave
imgen campaign route show spring_wave ocean_luxury --json
imgen campaign placement list spring_wave
imgen campaign placement remove spring_wave meta_square_awareness
```

### Generate campaign placements

```bash
imgen campaign generate spring_wave \
  --routes ocean_luxury,capsule_wardrobe \
  --placements meta_square_awareness \
  --variants 3 \
  --generator mock \
  --json
```

The command derives prompts from each route, produces deterministic seeds per placement, writes images inside `images/<route>/<placement>/`, caches thumbnails under `thumbnails/`, and upserts `placements/<placement>/manifest.json` with route summaries, variant metadata, and review states (default `pending`).

### Deterministic batch runs

Create a spec scaffold directly from campaign metadata:

```bash
imgen campaign batch-scaffold spring_wave \
  --routes ocean_luxury,capsule_wardrobe \
  --placements meta_square_awareness,meta_story_vertical \
  --variants 1 \
  --provider mock
```

Then execute it deterministically:

```bash
imgen campaign batch spring_wave --spec campaigns/spring_wave/batch.yaml --generator mock
```

Every generation event is recorded to `logs/batch-<timestamp>.jsonl` so CI/automation clients receive structured status updates. Use `--summary-only` (with `generate`, `batch`, or `export`) for concise human-readable output when you do not need the default detailed logs.

### Review states

```bash
imgen campaign review spring_wave \
  --route ocean_luxury \
  --placement meta_square_awareness \
  --variant 0 \
  --state approved \
  --notes "Matches legal copy"
```

Review changes propagate back into the placement manifest—exports can then filter on `approved`, `pending`, or `revise` states.

### Export bundles

```bash
imgen campaign export spring_wave \
  --platform meta_ads \
  --include approved \
  --output exports/spring_wave-meta.zip
```

Exports gather approved variants, compute checksums, write a platform CSV inventory, and emit a manifest at `exports/meta_ads/<timestamp>/manifest.json`. Pass an `--output` path to create a zip; otherwise the directory tree remains available for inspection.

> Slot and campaign commands can run inside the same repository—campaign mode is enabled per `campaign.yaml` without disrupting existing slot automation.

## AI SDK bridge

The CLI calls OpenRouter directly over HTTPS and defaults to the `google/gemini-2.5-flash-image-preview` model. Configure `OPENROUTER_API_KEY` in `.env` before running `imgen gen`. Optional headers (like `IMAGEMCP_OPENROUTER_HTTP_REFERER` and `IMAGEMCP_OPENROUTER_APP_TITLE`) and concurrency (`IMAGEMCP_OPENROUTER_MAX_WORKERS`) can also be set via environment variables. If you prefer calling Google directly, set `--provider google` (or `IMAGEMCP_DEFAULT_PROVIDER=google`)—note that the pure-Python generator currently supports OpenRouter only.

## Gallery server

Run the local gallery to browse variants from the browser:

```bash
imgen gallery serve --target-root public/img --port 8765 --open-browser
```

The gallery binds to `localhost`, now featuring two modes:

- **Slots** — the original session browser with promotion controls and metadata dumping.
- **Campaigns** — a campaign dashboard showing route/placement matrices, review-state filters, export history, and quick review toggles that write directly to placement manifests.

The CLI always prints the expected gallery URL so agents can surface it to users. When you are finished with a slot, open its detail view and use the **Delete slot** action to remove the promoted asset along with all recorded sessions—handy for clearing temporary experiments while keeping other slots intact.

## FastMCP planner

`server.py` exposes both slot and campaign tooling for agents:

- `collect_context_questions`: identifies missing slot context, provides sensible defaults, and highlights provider constraints (size vs aspect ratio, seeds, etc.).
- `plan_image_job`: returns an AI generation plan along with a CLI command template and stdin payload ready for execution by the local CLI.
- `collect_campaign_brief`: reports missing campaign-brief fields, returns defaults (generator/provider/variants), and previews bundled placement templates.
- `plan_campaign_routes`: emits normalized CLI action lists to initialize a campaign, add routes/placements, run generation, and export approved assets.
- `plan_batch_generation`: scaffolds deterministic batch specs, runs them, and exports results using the same CLI-action contract.

Run the planner locally during development:

```bash
python server.py
```

Agents that receive the planner response can call `imagemcp.campaign.orchestrator.execute_cli_actions` to run the returned commands locally; the helper streams `[imagemcp] step=...` logs and halts on the first non-zero exit code.

## Testing

Install the test extras and run `pytest`:

```bash
uv pip install -e .[dev]
pytest
```

The tests cover end-to-end CLI behaviour (generation + selection) and planning logic.

## Notes

- The default generator uses OpenRouter's HTTP API with the `google/gemini-2.5-flash-image-preview` model. Provide `OPENROUTER_API_KEY` in `.env`. To call Google directly, switch the `--provider` flag or set `IMAGEMCP_DEFAULT_PROVIDER=google` (direct Google support is not yet implemented in the pure-Python generator).
- You can still opt into the local mock generator for offline testing via `--generator mock`.
- All file operations enforce project-root scoping and use atomic promotion to keep dev servers stable.
- Update `.env.example` if new environment variables are introduced. Secrets must never be committed.
