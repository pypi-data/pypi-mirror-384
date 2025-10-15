from __future__ import annotations

import base64
import json
import os
import random
from concurrent.futures import ThreadPoolExecutor
from ._compat import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Set, Tuple

import hashlib

from PIL import Image, ImageDraw, ImageFont
import httpx

try:
    _LANCZOS = Image.Resampling.LANCZOS  # Pillow >= 10
except AttributeError:  # pragma: no cover - older Pillow fallback
    _LANCZOS = Image.LANCZOS

_DEFAULT_SIZE = (1024, 1024)

_PLACEHOLDER_PATTERNS = (
    "todo: fill prompt",
    "todo: fill summary",
    "todo: fill campaign objective",
    "todo: update campaign objective",
)

_MAX_TEXT_ONLY_RETRIES = 3


def _detect_placeholder_prompt(prompt: str) -> Optional[str]:
    normalized = (prompt or "").strip().lower()
    if not normalized:
        return None
    for pattern in _PLACEHOLDER_PATTERNS:
        if pattern in normalized:
            return pattern
    if "todo" in normalized:
        return "todo"
    return None


class ProviderExecutionError(RuntimeError):
    """Raised when an upstream provider cannot complete an image request."""

    def __init__(
        self,
        *,
        provider: str,
        generator: str,
        message: str,
        status: Optional[int] = None,
        body: Optional[str] = None,
        context: Optional[Dict[str, object]] = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.generator = generator
        self.status = status
        self.body = body
        self.context: Dict[str, object] = context.copy() if context else {}

    def attach_context(self, extra: Dict[str, object]) -> None:
        for key, value in extra.items():
            self.context.setdefault(key, value)


def _truncate(text: str, limit: int = 2000) -> str:
    snippet = text.strip()
    if len(snippet) <= limit:
        return snippet
    return snippet[: limit - 1] + "…"


class ImageGenerator(Protocol):
    def generate(
        self,
        prompt: str,
        n: int,
        *,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        seed: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        provider_options: Optional[Dict[str, object]] = None,
    ) -> "GenerationResult":
        ...


@dataclass()
class GeneratedImageArtifacts:
    filename: str
    processed_path: Path
    media_type: str
    processed_width: int
    processed_height: int
    raw_filename: Optional[str]
    raw_path: Optional[Path]
    original_width: Optional[int]
    original_height: Optional[int]
    crop_fraction: Optional[float]


@dataclass()
class GenerationResult:
    images: List[GeneratedImageArtifacts]
    warnings: List[str]

    @property
    def image_paths(self) -> List[Path]:
        return [artifact.processed_path for artifact in self.images]


class MockImageGenerator:
    """Generate placeholder images locally without hitting external APIs."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(
        self,
        prompt: str,
        n: int,
        *,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        seed: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        provider_options: Optional[Dict[str, object]] = None,
    ) -> GenerationResult:
        width, height, warnings = _resolve_dimensions(size, aspect_ratio)
        rng = _stable_random(seed)
        base_color = _color_from_prompt(prompt)
        artifacts: List[GeneratedImageArtifacts] = []
        for index in range(n):
            variant_color = _shift_color(base_color, rng.randint(-40, 40))
            image = Image.new("RGB", (width, height), variant_color)
            draw = ImageDraw.Draw(image)
            overlay_text = _truncate_overlay(prompt, 120) or "(empty prompt)"
            info_text = f"{model or provider or 'mock'} #{index + 1}"
            _draw_text(draw, overlay_text, (width, height), headline=True)
            _draw_text(draw, info_text, (width, height), headline=False, y_offset=height - 80)
            filename = f"{index}.png"
            path = self.output_dir / filename
            image.save(path, format="PNG")
            artifacts.append(
                GeneratedImageArtifacts(
                    filename=filename,
                    processed_path=path,
                    media_type="image/png",
                    processed_width=width,
                    processed_height=height,
                    raw_filename=None,
                    raw_path=None,
                    original_width=width,
                    original_height=height,
                    crop_fraction=None,
                )
            )
        return GenerationResult(images=artifacts, warnings=warnings)


class OpenRouterGenerator:
    """Call the OpenRouter HTTP API directly to produce image outputs."""

    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OpenRouter API key is missing. Set OPENROUTER_API_KEY in your environment."
            )
        self.api_key = api_key
        base_url = os.environ.get("IMAGEMCP_OPENROUTER_BASE_URL", "https://openrouter.ai")
        base_url = base_url.rstrip("/")
        if not base_url.endswith("/api/v1"):
            base_url = f"{base_url}/api/v1"
        self.api_url = f"{base_url}/chat/completions"
        self.extra_headers: Dict[str, str] = {}
        referer = os.environ.get("IMAGEMCP_OPENROUTER_HTTP_REFERER") or os.environ.get("OPENROUTER_HTTP_REFERER")
        if referer:
            self.extra_headers["HTTP-Referer"] = referer
        title = os.environ.get("IMAGEMCP_OPENROUTER_APP_TITLE") or os.environ.get("OPENROUTER_X_TITLE")
        if title:
            self.extra_headers["X-Title"] = title
        self.timeout = float(os.environ.get("IMAGEMCP_OPENROUTER_TIMEOUT", "60"))
        self.max_workers = max(1, int(os.environ.get("IMAGEMCP_OPENROUTER_MAX_WORKERS", "4")))
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        headers.update(self.extra_headers)
        self.client = httpx.Client(timeout=self.timeout, headers=headers, http2=True)

    def generate(
        self,
        prompt: str,
        n: int,
        *,
        size: Optional[str] = None,
        aspect_ratio: Optional[str] = None,
        seed: Optional[int] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        provider_options: Optional[Dict[str, object]] = None,
    ) -> GenerationResult:
        if not prompt:
            raise RuntimeError("Prompt is required for image generation.")

        if provider and provider.lower() == "google":
            raise RuntimeError("Direct Google provider is not supported in the pure Python generator. Use OpenRouter instead.")

        total = max(1, int(n) if n else 1)
        normalized_options = json.loads(json.dumps(provider_options or {}))
        provider_key = "openrouter"
        provider_config = normalized_options.get(provider_key) or {}

        has_aspect_ratio = bool(aspect_ratio)
        if has_aspect_ratio:
            provider_config.pop("size", None)
            provider_config.setdefault("aspectRatio", aspect_ratio)
        elif size and provider_config.get("size") is None:
            provider_config["size"] = size
        if seed is not None and provider_config.get("seed") is None:
            provider_config["seed"] = seed
        normalized_options[provider_key] = provider_config

        reference_image = _build_reference_image_payload(size, aspect_ratio)
        warnings: List[str] = []
        provider_metadata: List[object] = []
        images: List[Dict[str, str]] = []
        last_response: Optional[Dict[str, object]] = None

        target_size = _parse_size_string(size)
        ratio_components = _parse_aspect_ratio(aspect_ratio)
        target_ratio = None
        if ratio_components is not None:
            target_ratio = ratio_components[0] / ratio_components[1]
        elif target_size is not None and target_size[1] != 0:
            target_ratio = target_size[0] / target_size[1]

        model_id = model or os.environ.get("IMAGEMCP_OPENROUTER_MODEL") or "google/gemini-2.5-flash-image-preview"
        provider_name = provider or provider_key
        request_context = {
            "model": model_id,
            "requested_total": total,
            "size": size,
            "aspect_ratio": aspect_ratio,
        }

        placeholder_token = _detect_placeholder_prompt(prompt)
        if placeholder_token:
            context = {
                **request_context,
                "reason": "placeholder_prompt",
                "placeholder_token": placeholder_token,
            }
            raise ProviderExecutionError(
                provider=provider_name,
                generator="openrouter",
                message=(
                    "Prompt still contains placeholder text (found '{token}'). "
                    "Replace the TODO copy with concrete image instructions before generating."
                ).format(token=placeholder_token),
                context=context,
            )

        max_text_retries = _MAX_TEXT_ONLY_RETRIES
        attempts = 0
        text_only_streak = 0
        aggregated_text_snippets: List[str] = []
        text_attempt_records: List[Dict[str, object]] = []
        last_failure_message: Optional[str] = None
        last_failure_reason = "empty_response"

        try:
            while len(images) < total:
                attempts += 1
                remaining = total - len(images)
                batch_size = min(remaining, self.max_workers)
                payloads = [
                    self._build_payload(prompt, model_id, provider_config, reference_image)
                    for _ in range(batch_size)
                ]
                responses = self._execute_batch(payloads) or []
                new_images = False
                attempt_snippets: List[str] = []
                attempt_reason: Optional[str] = None
                attempt_detail: Optional[str] = None

                for response in responses:
                    if response is None:
                        continue
                    last_response = response
                    resp_images, resp_warnings, resp_metadata = self._consume_response(response)
                    if resp_warnings:
                        warnings.extend(resp_warnings)
                    if resp_metadata:
                        provider_metadata.extend(resp_metadata)
                    if resp_images:
                        images.extend(resp_images)
                        new_images = True
                        if len(images) >= total:
                            break
                        continue

                    reason, detail, text_snippets = _diagnose_no_image_response(response)
                    attempt_reason = attempt_reason or reason
                    if detail and not attempt_detail:
                        attempt_detail = detail
                    if text_snippets:
                        attempt_snippets.extend(text_snippets)

                if new_images:
                    text_only_streak = 0
                    continue

                text_only_streak += 1
                if attempt_reason:
                    last_failure_reason = attempt_reason
                if attempt_detail:
                    last_failure_message = attempt_detail
                if attempt_snippets:
                    aggregated_text_snippets.extend(attempt_snippets)

                record: Dict[str, object] = {
                    "attempt": attempts,
                    "reason": attempt_reason or "empty_response",
                }
                if attempt_detail:
                    record["detail"] = attempt_detail
                if attempt_snippets:
                    record["text"] = attempt_snippets
                text_attempt_records.append(record)

                if text_only_streak > max_text_retries:
                    break

            if not images:
                debug_message = ""
                if last_response is not None:
                    try:
                        debug_message = json.dumps(last_response, indent=2)
                    except Exception:
                        debug_message = str(last_response)

                failure_message = last_failure_message
                if failure_message:
                    message_text = failure_message
                else:
                    message_text = "OpenRouter did not return any image files."
                if attempts:
                    message_text += " Ensure the prompt is an image-generation request and try again."

                context = {
                    **request_context,
                    "reason": last_failure_reason,
                    "attempts": attempts,
                    "text_only_attempts": text_only_streak,
                    "max_text_only_retries": max_text_retries,
                }
                if aggregated_text_snippets:
                    context["response_text"] = aggregated_text_snippets
                if text_attempt_records:
                    context["response_text_attempts"] = text_attempt_records
                raise ProviderExecutionError(
                    provider=provider_name,
                    generator="openrouter",
                    message=message_text,
                    body=_truncate(debug_message) if debug_message else None,
                    context=context,
                )
        except ProviderExecutionError as exc:
            exc.attach_context(request_context)
            raise
        except Exception as exc:
            raise ProviderExecutionError(
                provider=provider_name,
                generator="openrouter",
                message=str(exc),
                context={**request_context, "reason": "unexpected_exception"},
            ) from exc

        artifacts: List[GeneratedImageArtifacts] = []
        for index, entry in enumerate(images[:total]):
            data_url = entry["data_url"]
            media_type = entry.get("media_type") or "image/png"
            extension = _extension_from_media_type(media_type)
            filename = f"{index}{extension}"
            base64_payload = data_url.split(",", 1)[1] if "," in data_url else data_url
            binary = _decode_base64_payload(base64_payload)
            raw_filename = f"{index}_raw{extension}"
            raw_path = self.output_dir / raw_filename
            raw_path.write_bytes(binary)

            crop_axis = None
            crop_fraction = 0.0
            processed_image = None
            original_width = None
            original_height = None
            with Image.open(BytesIO(binary)) as pil_image:
                pil_image.load()
                original_width, original_height = pil_image.size
                processed_image, crop_axis, crop_fraction = _apply_post_processing(
                    pil_image,
                    target_ratio,
                    target_size,
                )

            processed_path = self.output_dir / filename
            _save_image(processed_image, processed_path, media_type)
            processed_width, processed_height = processed_image.size
            processed_image.close()

            if crop_axis and crop_fraction and crop_fraction > 0:
                severity = "Significant " if crop_fraction > 0.2 else ""
                warnings.append(
                    f"{severity}crop applied to image #{index}: trimmed {crop_fraction:.1%} of its {crop_axis} to enforce aspect ratio ({original_width}x{original_height} -> {processed_width}x{processed_height})."
                )

            artifacts.append(
                GeneratedImageArtifacts(
                    filename=filename,
                    processed_path=processed_path,
                    media_type=media_type,
                    processed_width=processed_width,
                    processed_height=processed_height,
                    raw_filename=raw_filename,
                    raw_path=raw_path,
                    original_width=original_width,
                    original_height=original_height,
                    crop_fraction=crop_fraction if crop_fraction else None,
                )
            )

        return GenerationResult(images=artifacts, warnings=warnings)

    def _build_payload(
        self,
        prompt: str,
        model_id: str,
        provider_config: Dict[str, object],
        reference_image: Optional[Dict[str, str]],
    ) -> Dict[str, object]:
        messages_content = []
        if reference_image and reference_image.get("dataUrl"):
            messages_content.append(
                {
                    "type": "image_url",
                    "image_url": {
                        "url": reference_image["dataUrl"],
                        "mime_type": reference_image.get("mediaType", "image/png"),
                    },
                }
            )
            text_segments = [prompt]
            if reference_image.get("instruction"):
                text_segments.append(reference_image["instruction"])
            text_segments.append("Do not change the aspect ratio shown in the reference image.")
        else:
            text_segments = [prompt]
        text_instruction = "\n\n".join(segment for segment in text_segments if segment)
        messages_content.append({"type": "text", "text": text_instruction})

        payload: Dict[str, object] = {
            "model": model_id,
            "messages": [
                {
                    "role": "user",
                    "content": messages_content,
                }
            ],
            "modalities": ["image", "text"],
        }
        if provider_config:
            payload["extra_body"] = json.loads(json.dumps(provider_config))
        return payload

    def _execute_batch(self, payloads: List[Dict[str, object]]) -> List[Optional[Dict[str, object]]]:
        if not payloads:
            return []
        if len(payloads) == 1:
            return [self._post_json(payloads[0])]

        results: List[Optional[Dict[str, object]]] = [None] * len(payloads)

        def worker(index: int, payload: Dict[str, object]) -> None:
            results[index] = self._post_json(payload)

        with ThreadPoolExecutor(max_workers=len(payloads)) as executor:
            futures = [executor.submit(worker, idx, payload) for idx, payload in enumerate(payloads)]
            for future in futures:
                future.result()
        return results

    def _consume_response(
        self, response: Dict[str, object]
    ) -> Tuple[List[Dict[str, str]], List[str], List[object]]:
        images: List[Dict[str, str]] = []
        warnings: List[str] = []
        metadata: List[object] = []

        if response.get("warnings"):
            warnings.extend(str(item) for item in response["warnings"])

        for choice in response.get("choices", []) or []:
            provider_meta = choice.get("provider")
            if provider_meta is not None:
                metadata.append(provider_meta)
            message = choice.get("message") or {}
            images.extend(_extract_images_from_message(message))
        return images, warnings, metadata

    def _post_json(self, payload: Dict[str, object]) -> Dict[str, object]:
        try:
            response = self.client.post(self.api_url, json=payload)
        except httpx.RequestError as exc:  # pragma: no cover - network dependent
            raise ProviderExecutionError(
                provider="openrouter",
                generator="openrouter",
                message="Failed to reach OpenRouter API.",
                context={
                    "reason": "network",
                    "url": self.api_url,
                    "error": str(exc),
                },
            ) from exc

        status = response.status_code
        if status >= 400:
            body = _truncate(response.text or "", limit=800)
            context = {
                "reason": "http_status",
                "url": self.api_url,
            }
            request_id = response.headers.get("x-request-id")
            if request_id:
                context["request_id"] = request_id
            retry_after = response.headers.get("retry-after")
            if retry_after:
                context["retry_after"] = retry_after
            raise ProviderExecutionError(
                provider="openrouter",
                generator="openrouter",
                message=f"OpenRouter API returned HTTP {status}",
                status=status,
                body=body,
                context=context,
            )

        try:
            return response.json()
        except ValueError as exc:
            raise ProviderExecutionError(
                provider="openrouter",
                generator="openrouter",
                message="OpenRouter response was not valid JSON.",
                status=status,
                body=_truncate(response.text or "", limit=800),
                context={"reason": "invalid_json", "url": self.api_url},
            ) from exc

    def close(self) -> None:
        try:
            self.client.close()
        except Exception:  # pragma: no cover - defensive cleanup
            pass


def _ensure_data_url(payload: str, media_type: Optional[str]) -> str:
    media = media_type or "image/png"
    cleaned = payload.strip()
    if cleaned.startswith("data:"):
        return cleaned
    return f"data:{media};base64,{cleaned}"


def _extract_images_from_message(message: Dict[str, object]) -> List[Dict[str, str]]:
    candidates: List[Dict[str, str]] = []
    images_section = message.get("images")
    if images_section:
        candidates.extend(_extract_images_from_content(images_section))
    candidates.extend(_extract_images_from_content(message.get("content")))
    candidates.extend(_extract_images_from_content(message.get("attachments")))
    candidates.extend(_extract_images_from_content(message.get("data")))

    deduped: List[Dict[str, str]] = []
    seen: Set[Tuple[str, str]] = set()
    for item in candidates:
        data_url = item.get("data_url")
        media_type = item.get("media_type") or "image/png"
        if not isinstance(data_url, str):
            continue
        normalized = data_url.strip()
        if not normalized:
            continue
        key = (normalized, media_type)
        if key in seen:
            continue
        seen.add(key)
        deduped.append({"data_url": normalized, "media_type": media_type})
    return deduped


def _diagnose_no_image_response(
    response: Dict[str, object]
) -> Tuple[str, Optional[str], List[str]]:
    if not isinstance(response, dict):  # Defensive guard
        return "empty_response", None, []

    text_snippets: List[str] = []
    finish_reasons: List[str] = []
    for choice in response.get("choices", []) or []:
        finish = choice.get("finish_reason") or choice.get("native_finish_reason")
        if isinstance(finish, str) and finish:
            finish_reasons.append(finish)
        message = choice.get("message") or {}
        text_snippets.extend(_extract_text_from_message(message))

    combined_text = " ".join(snippet for snippet in text_snippets if snippet)
    normalized_text = combined_text.lower().strip()

    reason = "empty_response"
    detail: Optional[str] = None
    if normalized_text:
        refusal_keywords = (
            "unable",
            "cannot",
            "can't",
            "not able",
            "policy",
            "safety",
            "refuse",
            "decline",
        )
        reason = (
            "content_policy"
            if any(keyword in normalized_text for keyword in refusal_keywords)
            else "provider_text_response"
        )
        snippet = _truncate(combined_text, 400)
        detail = f"OpenRouter returned text instead of images: {snippet}"
        if finish_reasons:
            detail += f" (finish_reason={','.join(finish_reasons)})"
    return reason, detail, text_snippets


def _extract_images_from_content(
    content: object, fallback_mime: str = "image/png"
) -> List[Dict[str, str]]:
    if isinstance(content, list):
        results: List[Dict[str, str]] = []
        for entry in content:
            results.extend(_extract_images_from_entry(entry, fallback_mime))
        return results
    if isinstance(content, dict):
        return _extract_images_from_entry(content, fallback_mime)
    return []


def _extract_images_from_entry(
    entry: object, fallback_mime: str = "image/png"
) -> List[Dict[str, str]]:
    results: List[Dict[str, str]] = []
    if not isinstance(entry, dict):
        return results

    media_type = entry.get("mime_type") or entry.get("media_type") or fallback_mime

    base64_candidates: List[Tuple[str, Optional[str]]] = []
    for key in ("image_base64", "b64_json", "base64"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            base64_candidates.append((value.strip(), media_type))

    for key in ("dataUrl", "data_url"):
        url_value = entry.get(key)
        if isinstance(url_value, str) and url_value.strip():
            results.append({"data_url": url_value.strip(), "media_type": media_type})

    image_url = entry.get("image_url") or entry.get("url")
    if isinstance(image_url, dict):
        url = image_url.get("url")
        if isinstance(url, str) and url.strip():
            results.append(
                {
                    "data_url": url.strip(),
                    "media_type": image_url.get("mime_type") or media_type,
                }
            )
    elif isinstance(image_url, str) and image_url.strip():
        results.append({"data_url": image_url.strip(), "media_type": media_type})

    urls_field = entry.get("urls")
    if isinstance(urls_field, list):
        for item in urls_field:
            if isinstance(item, str) and item.strip():
                results.append({"data_url": item.strip(), "media_type": media_type})
            elif isinstance(item, dict):
                maybe_url = item.get("url")
                if isinstance(maybe_url, str) and maybe_url.strip():
                    results.append(
                        {
                            "data_url": maybe_url.strip(),
                            "media_type": item.get("mime_type") or media_type,
                        }
                    )

    inline_data = entry.get("inline_data")
    if isinstance(inline_data, dict):
        inline_mime = inline_data.get("mime_type") or media_type
        payload = inline_data.get("data")
        if isinstance(payload, str) and payload.strip():
            base64_candidates.append((payload.strip(), inline_mime))
        base64_candidates.extend(
            _collect_base64_candidates_from_dict(inline_data, inline_mime)
        )

    data_field = entry.get("data")
    if isinstance(data_field, dict):
        data_mime = data_field.get("mime_type") or data_field.get("media_type") or media_type
        base64_candidates.extend(
            _collect_base64_candidates_from_dict(data_field, data_mime)
        )
        for key in ("dataUrl", "data_url"):
            val = data_field.get(key)
            if isinstance(val, str) and val.strip():
                results.append({"data_url": val.strip(), "media_type": data_mime})
        results.extend(_extract_images_from_content(data_field.get("content"), data_mime))

    for payload, mime in base64_candidates:
        results.append({"data_url": _ensure_data_url(payload, mime), "media_type": mime or fallback_mime})

    for nested_key in ("content", "attachments", "output", "outputs", "results", "parts"):
        nested = entry.get(nested_key)
        if nested:
            results.extend(_extract_images_from_content(nested, media_type))

    return results


def _collect_base64_candidates_from_dict(
    payload: Dict[str, object], default_mime: Optional[str]
) -> List[Tuple[str, Optional[str]]]:
    results: List[Tuple[str, Optional[str]]] = []
    for key in ("image_base64", "b64_json", "base64", "data"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            results.append((value.strip(), payload.get("mime_type") or payload.get("media_type") or default_mime))
    return results


def _extract_text_from_message(message: Dict[str, object]) -> List[str]:
    if not isinstance(message, dict):
        return []
    results: List[str] = []
    content = message.get("content")
    results.extend(_extract_text_from_content(content))
    text_field = message.get("text")
    if isinstance(text_field, str) and text_field.strip():
        results.append(text_field.strip())
    data_field = message.get("data")
    if data_field:
        results.extend(_extract_text_from_content(data_field))
    return [segment for segment in results if segment]


def _extract_text_from_content(content: object) -> List[str]:
    if isinstance(content, str):
        return [content.strip()]
    if isinstance(content, list):
        results: List[str] = []
        for entry in content:
            results.extend(_extract_text_from_entry(entry))
        return results
    if isinstance(content, dict):
        return _extract_text_from_entry(content)
    return []


def _extract_text_from_entry(entry: object) -> List[str]:
    if isinstance(entry, str):
        stripped = entry.strip()
        return [stripped] if stripped else []
    if not isinstance(entry, dict):
        return []

    results: List[str] = []
    text_field = entry.get("text")
    if isinstance(text_field, str) and text_field.strip():
        results.append(text_field.strip())

    for key in ("title", "summary", "content"):
        value = entry.get(key)
        if isinstance(value, str) and value.strip():
            results.append(value.strip())
        elif value:
            results.extend(_extract_text_from_content(value))

    for nested_key in ("output", "outputs", "parts", "messages", "segments"):
        nested = entry.get(nested_key)
        if nested:
            results.extend(_extract_text_from_content(nested))

    return results


def build_generator(output_dir: Path, kind: Optional[str] = None) -> ImageGenerator:
    normalized = (kind or "openrouter").lower()
    if normalized == "mock":
        return MockImageGenerator(output_dir)
    if normalized in {"ai-sdk", "google", "gemini", "openrouter"}:
        return OpenRouterGenerator(output_dir)
    raise ValueError(f"Unsupported generator kind '{kind}'.")


def _extension_from_media_type(media_type: str) -> str:
    if media_type == "image/jpeg":
        return ".jpg"
    if media_type == "image/webp":
        return ".webp"
    return ".png"


def _decode_base64_payload(payload: str) -> bytes:
    if payload.startswith("data:"):
        try:
            _, encoded = payload.split(",", 1)
        except ValueError:
            encoded = payload
    else:
        encoded = payload
    return base64.b64decode(encoded)


def _parse_size_string(size: Optional[str]) -> Optional[Tuple[int, int]]:
    if not size:
        return None
    try:
        width_str, height_str = size.lower().split("x", 1)
        width = int(width_str)
        height = int(height_str)
        if width <= 0 or height <= 0:
            return None
        return width, height
    except Exception:
        return None


def _parse_aspect_ratio(aspect_ratio: Optional[str]) -> Optional[Tuple[int, int]]:
    if not aspect_ratio:
        return None
    try:
        width_str, height_str = aspect_ratio.split(":", 1)
        width = int(width_str)
        height = int(height_str)
        if width <= 0 or height <= 0:
            return None
        return width, height
    except Exception:
        return None


def _apply_post_processing(
    image: Image.Image,
    target_ratio: Optional[float],
    target_size: Optional[Tuple[int, int]],
) -> Tuple[Image.Image, Optional[str], float]:
    working = image.copy()
    crop_axis: Optional[str] = None
    crop_fraction = 0.0

    if target_ratio is not None:
        working, crop_axis, crop_fraction = _crop_to_aspect(working, target_ratio)

    if target_size is not None:
        working = working.resize(target_size, _LANCZOS)

    return working, crop_axis, crop_fraction


def _crop_to_aspect(image: Image.Image, target_ratio: float) -> Tuple[Image.Image, Optional[str], float]:
    width, height = image.size
    if width <= 0 or height <= 0 or target_ratio <= 0:
        return image, None, 0.0

    current_ratio = width / height
    if not _needs_aspect_correction(current_ratio, target_ratio):
        return image, None, 0.0

    working = image
    crop_axis: Optional[str] = None
    crop_fraction = 0.0

    if current_ratio > target_ratio:
        new_width = max(1, int(round(height * target_ratio)))
        new_width = min(new_width, width)
        delta = width - new_width
        left = max(0, delta // 2)
        right = left + new_width
        working = working.crop((left, 0, right, height))
        crop_axis = "width"
        crop_fraction = delta / width if width else 0.0
    else:
        new_height = max(1, int(round(width / target_ratio)))
        new_height = min(new_height, height)
        delta = height - new_height
        top = max(0, delta // 2)
        bottom = top + new_height
        working = working.crop((0, top, width, bottom))
        crop_axis = "height"
        crop_fraction = delta / height if height else 0.0

    return working, crop_axis, crop_fraction


def _needs_aspect_correction(current_ratio: float, target_ratio: float, tolerance: float = 0.005) -> bool:
    if current_ratio <= 0 or target_ratio <= 0:
        return False
    return abs(current_ratio - target_ratio) / target_ratio > tolerance


def _save_image(image: Image.Image, path: Path, media_type: str) -> None:
    format_hint = _format_from_media_type(media_type)
    target = image
    if format_hint == "JPEG" and image.mode in {"RGBA", "LA", "P"}:
        target = image.convert("RGB")
    try:
        if format_hint:
            target.save(path, format_hint)
        else:
            target.save(path)
    finally:
        if target is not image:
            target.close()


def _format_from_media_type(media_type: str) -> Optional[str]:
    media_type = media_type.lower()
    if media_type == "image/png":
        return "PNG"
    if media_type in {"image/jpeg", "image/jpg"}:
        return "JPEG"
    if media_type == "image/webp":
        return "WEBP"
    return None


def _build_reference_image_payload(size: Optional[str], aspect_ratio: Optional[str]) -> Optional[Dict[str, str]]:
    dimensions = _dimensions_from_size_or_ratio(size, aspect_ratio)
    if dimensions is None:
        return None
    width, height = dimensions
    if width <= 0 or height <= 0:
        return None
    image = Image.new("RGBA", (width, height), (128, 128, 128, 252))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    base64_data = base64.b64encode(buffer.getvalue()).decode("ascii")
    data_url = f"data:image/png;base64,{base64_data}"
    return {
        "dataUrl": data_url,
        "mediaType": "image/png",
        "instruction": "Use the attached transparent image to match the final aspect ratio.",
    }


def _dimensions_from_size_or_ratio(
    size: Optional[str], aspect_ratio: Optional[str]
) -> Optional[Tuple[int, int]]:
    parsed_size = _parse_size_string(size)
    if parsed_size is not None:
        width, height = parsed_size
        return max(width, 1), max(height, 1)
    ratio_parts = _parse_aspect_ratio(aspect_ratio)
    if ratio_parts is not None:
        w, h = ratio_parts
        base = 1024
        width = base
        height = max(1, int(round(base * h / w)))
        return width, height
    return None


def _resolve_dimensions(size: Optional[str], aspect_ratio: Optional[str]) -> tuple[int, int, List[str]]:
    warnings: List[str] = []
    if size and aspect_ratio:
        warnings.append("Both size and aspect_ratio provided; using size per AI SDK rules.")
    if size:
        try:
            width_str, height_str = size.lower().split("x")
            width = int(width_str)
            height = int(height_str)
            return width, height, warnings
        except Exception as exc:  # pragma: no cover - defensive
            warnings.append(f"Invalid size '{size}': {exc}")
    if aspect_ratio:
        parts = aspect_ratio.split(":")
        if len(parts) == 2:
            try:
                width_ratio = int(parts[0])
                height_ratio = int(parts[1])
                base = 1024
                width = base
                height = max(1, int(base * height_ratio / width_ratio))
                return width, height, warnings
            except Exception as exc:  # pragma: no cover
                warnings.append(f"Invalid aspect ratio '{aspect_ratio}': {exc}")
    return _DEFAULT_SIZE[0], _DEFAULT_SIZE[1], warnings


def _color_from_prompt(prompt: str) -> tuple[int, int, int]:
    digest = hashlib.sha256(prompt.encode("utf-8")).digest()
    return digest[0], digest[1], digest[2]


def _shift_color(color: tuple[int, int, int], delta: int) -> tuple[int, int, int]:
    return tuple(max(0, min(255, channel + delta)) for channel in color)


def _truncate_overlay(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def _draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    size: tuple[int, int],
    *,
    headline: bool,
    y_offset: Optional[int] = None,
) -> None:
    font = _get_font(36 if headline else 24)
    width, height = size
    bbox = draw.multiline_textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = max(10, (width - text_width) // 2)
    y = y_offset if y_offset is not None else max(10, (height - text_height) // 2)
    draw.multiline_text((x, y), text, fill=(255, 255, 255), font=font)


def _get_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("Arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def _stable_random(seed: Optional[int]) -> random.Random:
    if seed is None:
        return random.Random()
    return random.Random(seed)


__all__ = [
    "ProviderExecutionError",
    "ImageGenerator",
    "MockImageGenerator",
    "AiSdkGenerator",
    "GeneratedImageArtifacts",
    "GenerationResult",
    "build_generator",
]
