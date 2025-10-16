from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO

BUFFER_SIZE = 1024 * 1024


def compute_sha256(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(BUFFER_SIZE), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_replace_bytes(data: bytes, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_path_str = tempfile.mkstemp(dir=str(destination.parent), prefix=".tmp")
    temp_path = Path(temp_path_str)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, destination)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def atomic_copy(source: Path, destination: Path) -> None:
    with source.open("rb") as fh:
        data = fh.read()
    atomic_replace_bytes(data, destination)


def copy_stream(stream: BinaryIO, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("wb") as fh:
        shutil.copyfileobj(stream, fh, BUFFER_SIZE)


__all__ = ["compute_sha256", "atomic_copy", "atomic_replace_bytes", "copy_stream"]
