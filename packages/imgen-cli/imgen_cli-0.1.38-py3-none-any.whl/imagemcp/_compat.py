"""Compatibility helpers for dataclasses with optional slots support."""

from __future__ import annotations

from dataclasses import dataclass as _dataclass


def slotted_dataclass(*args, **kwargs):
    """Wrap dataclass to prefer slots, but fall back if unsupported."""
    kwargs.setdefault("slots", True)
    try:
        return _dataclass(*args, **kwargs)
    except TypeError:
        kwargs.pop("slots", None)
        return _dataclass(*args, **kwargs)


# Expose as `dataclass` so callers can `from ._compat import dataclass`.
dataclass = slotted_dataclass

__all__ = ["dataclass"]
