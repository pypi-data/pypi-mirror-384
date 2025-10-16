from __future__ import annotations

import secrets
from datetime import datetime
from typing import Optional


def make_session_id(hint: Optional[str] = None) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    suffix = secrets.token_hex(3)
    if hint:
        safe_hint = _slugify(hint)
        if safe_hint:
            return f"{timestamp}-{safe_hint}-{suffix}"
    return f"{timestamp}-{suffix}"


def _slugify(value: str) -> str:
    allowed = [ch for ch in value.lower() if ch.isalnum() or ch in {"-", "_"}]
    return "".join(allowed).strip("-")


__all__ = ["make_session_id"]
