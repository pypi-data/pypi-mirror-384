from __future__ import annotations

import os
from typing import Dict, List

DEFAULT_PROVIDER = os.environ.get("IMAGEMCP_DEFAULT_PROVIDER", "openrouter")
DEFAULT_GENERATOR = os.environ.get("IMAGEMCP_DEFAULT_GENERATOR", "openrouter")
_ENV_DEFAULT_MODEL = os.environ.get("IMAGEMCP_DEFAULT_MODEL")
_OPENROUTER_MODEL = os.environ.get(
    "IMAGEMCP_OPENROUTER_MODEL", "google/gemini-2.5-flash-image-preview"
)
_GOOGLE_MODEL = os.environ.get("IMAGEMCP_GOOGLE_MODEL", "gemini-2.5-flash-image-preview")

SUPPORTED_MODELS: Dict[str, List[str]] = {
    "openrouter": [_OPENROUTER_MODEL],
    "mock": ["mock/image"],
}


def default_model_for_provider(provider: str | None = None) -> str:
    if _ENV_DEFAULT_MODEL:
        return _ENV_DEFAULT_MODEL
    key = (provider or DEFAULT_PROVIDER or "").strip().lower()
    if key == "google":
        return _GOOGLE_MODEL
    return _OPENROUTER_MODEL


def available_models() -> Dict[str, List[str]]:
    return {name: models[:] for name, models in SUPPORTED_MODELS.items()}


__all__ = [
    "DEFAULT_GENERATOR",
    "DEFAULT_PROVIDER",
    "default_model_for_provider",
    "available_models",
    "SUPPORTED_MODELS",
]
