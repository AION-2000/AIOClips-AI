"""AIOClips local highlight workflow for video footage with usage rights.

The source is an existing local file, not a scraped YouTube or social-media URL.
Authorization is self-declared and must be verified by a human before publishing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from .captions import write_animated_captions
from .highlights import detect_scene_changes, suggest_highlights
from .match_clips import Moment, detect_loud_moments, duration_seconds, render_short


class FootageRights(str, Enum):
    OWNED = "owned"
    LICENSED = "licensed"
    PUBLIC_DOMAIN = "public_domain"
    COMPATIBLE_CREATIVE_COMMONS = "compatible_creative_commons"


@dataclass(frozen=True)
class FootageDeclaration:
    rights: FootageRights
    evidence: str
    permission_to_publish: bool

    def validate(self) -> None:
        if not self.permission_to_publish:
            raise ValueError("Publishing rights must be confirmed")
        if not self.evidence.strip() or len(self.evidence) > 1000:
            raise ValueError("Provide a source or rights evidence reference")


def suggest_video_moments(
    source: Path, *, clip_seconds: float = 20.0, limit: int = 5
) -> list[Moment]:
    """Suggest energetic moments in any video, not only football.

    First use audio energy; fall back to scene transitions for silent footage.
    These are suggestions, NOT semantic descriptions of goals or other events.
    """
    if not 1 <= limit <= 20 or not math.isfinite(clip_seconds) or not 1 <= clip_seconds <= 180:
        raise ValueError("Invalid clip suggestion settings")
    duration = duration_seconds(source)
    moments = detect_loud_moments(source, max_clips=limit, clip_seconds=clip_seconds)
    if moments:
        return moments
    cuts = detect_scene_changes(str(source), timeout=300)
    candidates = suggest_highlights(duration, cuts, clip_length=clip_seconds, limit=limit)
    return [
        Moment(c.start, min(duration, c.start + c.duration), c.score, "scene_activity")
        for c in candidates
    ]


def make_review_clip(
    source: Path,
    output: Path,
    *,
    start: float,
    end: float,
    rights: FootageDeclaration,
    headline: str,
    caption_script: str,
    narration_audio: Path | None = None,
    size: tuple[int, int] = (1080, 1920),
) -> Path:
    """Render an authorized draft Short. Does NOT publish or certify clearance."""
    rights.validate()
    if not caption_script.strip():
        raise ValueError("Review captions cannot be blank")
    if output.resolve() == source.resolve():
        raise ValueError("Output cannot overwrite source footage")
    captions = output.with_suffix(".ass")
    write_animated_captions(caption_script, end - start, captions)
    render_short(
        source, output, start, end, headline, narration_audio, captions,
        width=size[0], height=size[1]
    )
    return output
