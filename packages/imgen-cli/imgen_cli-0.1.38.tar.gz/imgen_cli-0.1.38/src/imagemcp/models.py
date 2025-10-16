from __future__ import annotations

from dataclasses import field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional

from ._compat import dataclass

ISO_FORMAT = "%Y-%m-%dT%H:%M:%SZ"
SCHEMA_VERSION = "image-slot-session@1"


def utc_now() -> datetime:
    return datetime.utcnow().replace(microsecond=0)


def format_ts(ts: datetime) -> str:
    return ts.strftime(ISO_FORMAT)


@dataclass()
class SlotConstraints:
    width: Optional[int] = None
    height: Optional[int] = None
    aspect_ratio: Optional[str] = None
    guidance: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        return {k: v for k, v in data.items() if v is not None}


@dataclass()
class SessionRequest:
    request_text: str
    created_by: str = "agent"

    def to_dict(self) -> Dict[str, Any]:
        return {"requestText": self.request_text, "createdBy": self.created_by}


@dataclass()
class EffectiveParameters:
    prompt: str
    n: int
    size: Optional[str] = None
    aspect_ratio: Optional[str] = None
    seed: Optional[int] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    generator: Optional[str] = None
    provider_options: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "prompt": self.prompt,
            "n": self.n,
            "size": self.size,
            "aspectRatio": self.aspect_ratio,
            "seed": self.seed,
            "provider": self.provider,
            "model": self.model,
            "generator": self.generator,
            "providerOptions": self.provider_options or {},
        }


@dataclass()
class ImageRecord:
    filename: str
    media_type: str
    width: int
    height: int
    sha256: str
    original_width: Optional[int] = None
    original_height: Optional[int] = None
    raw_filename: Optional[str] = None
    crop_fraction: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "filename": self.filename,
            "mediaType": self.media_type,
            "width": self.width,
            "height": self.height,
            "sha256": self.sha256,
        }
        if self.original_width is not None:
            data["originalWidth"] = self.original_width
        if self.original_height is not None:
            data["originalHeight"] = self.original_height
        if self.raw_filename is not None:
            data["rawFilename"] = self.raw_filename
        if self.crop_fraction is not None:
            data["cropFraction"] = self.crop_fraction
        return data


@dataclass()
class HistoryRecord:
    index: int
    at: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {"index": self.index, "at": format_ts(self.at)}


@dataclass()
class SessionManifest:
    slot: str
    session_id: str
    target_path: str
    session_dir: str
    request: SessionRequest
    effective: EffectiveParameters
    images: List[ImageRecord]
    selected_index: int
    selected_path: str
    created_at: datetime
    completed_at: datetime
    history: List[HistoryRecord] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    schema: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema": self.schema,
            "slot": self.slot,
            "sessionId": self.session_id,
            "targetPath": self.target_path,
            "sessionDir": self.session_dir,
            "request": self.request.to_dict(),
            "effective": self.effective.to_dict(),
            "images": [img.to_dict() for img in self.images],
            "selectedIndex": self.selected_index,
            "selectedPath": self.selected_path,
            "history": [entry.to_dict() for entry in self.history],
            "warnings": self.warnings,
            "timestamps": {
                "createdAt": format_ts(self.created_at),
                "completedAt": format_ts(self.completed_at),
            },
        }

    def record_selection(self, index: int, at: Optional[datetime] = None) -> None:
        self.selected_index = index
        if at is None:
            at = utc_now()
        self.history.append(HistoryRecord(index=index, at=at))

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionManifest":
        timestamps = data.get("timestamps", {})
        created_at = datetime.strptime(timestamps["createdAt"], ISO_FORMAT)
        completed_at = datetime.strptime(timestamps["completedAt"], ISO_FORMAT)
        history = [
            HistoryRecord(
                index=item["index"],
                at=datetime.strptime(item["at"], ISO_FORMAT),
            )
            for item in data.get("history", [])
        ]
        images = [
            ImageRecord(
                filename=img["filename"],
                media_type=img["mediaType"],
                width=img["width"],
                height=img["height"],
                sha256=img["sha256"],
                original_width=img.get("originalWidth"),
                original_height=img.get("originalHeight"),
                raw_filename=img.get("rawFilename"),
                crop_fraction=img.get("cropFraction"),
            )
            for img in data.get("images", [])
        ]
        request_data = data.get("request", {})
        effective_data = data.get("effective", {})
        return cls(
            schema=data.get("schema", SCHEMA_VERSION),
            slot=data["slot"],
            session_id=data["sessionId"],
            target_path=data["targetPath"],
            session_dir=data["sessionDir"],
            request=SessionRequest(
                request_text=request_data.get("requestText", ""),
                created_by=request_data.get("createdBy", "agent"),
            ),
            effective=EffectiveParameters(
                prompt=effective_data.get("prompt", ""),
                n=effective_data.get("n", 0),
                size=effective_data.get("size"),
                aspect_ratio=effective_data.get("aspectRatio"),
                seed=effective_data.get("seed"),
                provider=effective_data.get("provider"),
                model=effective_data.get("model"),
                generator=effective_data.get("generator"),
                provider_options=effective_data.get("providerOptions", {}),
            ),
            images=images,
            selected_index=data.get("selectedIndex", 0),
            selected_path=data.get("selectedPath", ""),
            created_at=created_at,
            completed_at=completed_at,
            history=history,
            warnings=data.get("warnings", []),
        )


__all__ = [
    "SlotConstraints",
    "SessionRequest",
    "EffectiveParameters",
    "ImageRecord",
    "HistoryRecord",
    "SessionManifest",
    "SCHEMA_VERSION",
    "utc_now",
    "format_ts",
]
