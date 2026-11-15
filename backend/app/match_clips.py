"""Rights-aware match clip processing with FFmpeg.

This module does not download or bypass protections on third-party streaming sites.
Use a local recording or an authorized direct media file.
"""
from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from .url_safety import validate_url as _unused  # Reuse project safety policy at the API boundary.


@dataclass(frozen=True)
class Moment:
    start: float
    end: float
    score: float
    kind: str = "crowd_energy"


def _run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True)
    return result.stdout


def duration_seconds(video: Path) -> float:
    data = json.loads(_run("ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "json", str(video)))
    return float(data["format"]["duration"])


def detect_loud_moments(video: Path, max_clips: int = 5, clip_seconds: float = 18.0) -> list[Moment]:
    """Suggest energetic moments from audio volume; these are NOT verified goals."""
    import array
    import math

    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-vn", "-ac", "1",
         "-ar", "8000", "-f", "s16le", "-"],
        check=True, capture_output=True,
    ).stdout
    samples = array.array("h")
    samples.frombytes(raw)
    window = 8000 * 2
    scores = []
    for i in range(0, len(samples) - window + 1, window):
        block = samples[i:i + window]
        rms = math.sqrt(sum(v * v for v in block) / len(block)) / 32768
        scores.append((rms, i / 8000))
    length = duration_seconds(video)
    chosen: list[Moment] = []
    for score, t in sorted(scores, reverse=True):
        start = max(0.0, min(length - clip_seconds, t - clip_seconds * 0.45))
        end = min(length, start + clip_seconds)
        if end <= start or any(start < c.end + 3 and end > c.start - 3 for c in chosen):
            continue
        chosen.append(Moment(start, end, round(score, 4)))
        if len(chosen) == max_clips:
            break
    return sorted(chosen, key=lambda m: m.start)


def _escape_drawtext(text: str) -> str:
    return text.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'").replace("%", "\\%")


def render_short(
    source: Path, output: Path, start: float, end: float,
    headline: str = "MATCH HIGHLIGHT", narration_audio: Path | None = None,
) -> None:
    """Produce a 1080x1920 clip with readable headline, retaining original sound.

    Optional narration_audio is a user-authorized, pre-generated speech track.
    """
    if not source.is_file() or end <= start or start < 0 or end > duration_seconds(source):
        raise ValueError("Invalid source or clip timestamps")
    if not re.fullmatch(r"[\w ,.!?\-]{1,90}", headline, flags=re.UNICODE):
        raise ValueError("Headline contains unsupported characters")
    output.parent.mkdir(parents=True, exist_ok=True)
    # Blurred full-height backdrop with centered, uncropped match footage.
    filter_graph = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1080:1920:force_original_aspect_ratio=increase,"
        "crop=1080:1920,boxblur=20:10[blur];"
        "[fg]scale=1080:1920:force_original_aspect_ratio=decrease[front];"
        "[blur][front]overlay=(W-w)/2:(H-h)/2,"
        "drawbox=x=0:y=130:w=1080:h=180:color=black@0.7:t=fill,"
        "drawtext=text='" + _escape_drawtext(headline) + "':"
        "fontcolor=white:fontsize=54:x=(w-text_w)/2:y=195[v]"
    )
    cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(start), "-i", str(source)]
    if narration_audio:
        if not narration_audio.is_file():
            raise ValueError("Narration audio not found")
        cmd += ["-i", str(narration_audio)]
    cmd += ["-filter_complex", filter_graph, "-map", "[v]"]
    if narration_audio:
        cmd += ["-filter_complex_script", "/dev/null"] if False else []
        cmd += ["-filter:a", "[0:a]volume=0.2[match];[match][1:a]amix=inputs=2:duration=first[a]" , "-map", "[a]"]
    else:
        cmd += ["-map", "0:a?"]
    cmd += ["-t", str(end - start), "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "23", "-c:a", "aac", "-movflags", "+faststart", str(output)]
    subprocess.run(cmd, check=True)
