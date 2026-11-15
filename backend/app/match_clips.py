"""Generic vertical clip rendering from locally accessible, authorized footage.

Audio energy is a heuristic for interesting moments, not semantic event/goal detection.
This module never downloads videos or determines copyright ownership.
"""
from __future__ import annotations

import array
import json
import math
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Moment:
    start: float
    end: float
    score: float
    kind: str = "high_energy"


def _run(*args: str) -> str:
    result = subprocess.run(args, check=True, capture_output=True, text=True, timeout=30)
    return result.stdout


def _probe(video: Path) -> dict:
    if not video.is_file():
        raise FileNotFoundError(str(video))
    return json.loads(_run(
        "ffprobe", "-v", "error", "-show_entries",
        "format=duration:stream=codec_type", "-of", "json", str(video)
    ))


def duration_seconds(video: Path) -> float:
    data = _probe(video)
    duration = float(data["format"]["duration"])
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Invalid source video duration")
    return duration


def has_audio(video: Path) -> bool:
    return any(s.get("codec_type") == "audio" for s in _probe(video).get("streams", []))


def detect_loud_moments(
    video: Path, max_clips: int = 5, clip_seconds: float = 18.0
) -> list[Moment]:
    """Read decoded audio in short chunks to avoid loading entire movies into RAM.

    Returns high-energy candidates only; a loud moment may not be the best moment.
    Silent videos yield an empty list; callers can use scene-change candidates.
    """
    if not 1 <= max_clips <= 20 or not math.isfinite(clip_seconds) or clip_seconds <= 0:
        raise ValueError("Invalid highlight options")
    duration = duration_seconds(video)
    if not has_audio(video):
        return []
    window_seconds = 2
    sample_rate = 8000
    chunk_bytes = sample_rate * window_seconds * 2
    process = subprocess.Popen(
        ["ffmpeg", "-nostdin", "-v", "error", "-i", str(video), "-vn", "-ac", "1",
         "-ar", str(sample_rate), "-f", "s16le", "-"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    scores: list[tuple[float, float]] = []
    assert process.stdout is not None
    try:
        index = 0
        while True:
            block = process.stdout.read(chunk_bytes)
            if not block:
                break
            # An incomplete final chunk is acceptable, but 16-bit samples need even bytes.
            samples = array.array("h")
            samples.frombytes(block[: len(block) - len(block) % 2])
            if samples:
                rms = math.sqrt(sum(float(v) * float(v) for v in samples) / len(samples)) / 32768
                scores.append((rms, index * window_seconds))
            index += 1
    finally:
        process.stdout.close()
        exit_code = process.wait(timeout=300)
    if exit_code:
        raise RuntimeError("FFmpeg could not decode the audio")
    length = min(duration, clip_seconds)
    chosen: list[Moment] = []
    for score, t in sorted(scores, reverse=True):
        start = max(0.0, min(duration - length, t - length * 0.4))
        end = min(duration, start + length)
        if end <= start or any(start < c.end + 2 and end > c.start - 2 for c in chosen):
            continue
        chosen.append(Moment(round(start, 2), round(end, 2), round(score, 4)))
        if len(chosen) >= max_clips:
            break
    return sorted(chosen, key=lambda moment: moment.start)


def _drawtext_escape(text: str) -> str:
    return (text.replace("\\", "\\\\").replace(":", "\\:")
            .replace("'", "\\'").replace("%", "\\%")
            .replace(",", "\\,").replace("[", "\\[")
            .replace("]", "\\]"))


def render_short(
    source: Path,
    output: Path,
    start: float,
    end: float,
    headline: str = "THE MOMENT",
    narration_audio: Path | None = None,
    captions_ass: Path | None = None,
    *,
    width: int = 1080,
    height: int = 1920,
) -> None:
    """Render a vertical MP4, optionally mixing narration and burning ASS captions.

    Center-crops neither the original video nor an individual's face: the entire
    source picture remains visible over a blurred vertical background.
    """
    duration = duration_seconds(source)
    if not all(math.isfinite(v) for v in (start, end)) or start < 0 or not start < end <= duration:
        raise ValueError("Invalid clip time range")
    if not re.fullmatch(r"[\w ,.!?\-]{1,90}", headline, flags=re.UNICODE):
        raise ValueError("Headline contains unsupported characters")
    if width < 128 or height < 128 or width % 2 or height % 2:
        raise ValueError("Output dimensions must be even and at least 128 pixels")
    if narration_audio is not None and not narration_audio.is_file():
        raise FileNotFoundError(str(narration_audio))
    if captions_ass is not None and not captions_ass.is_file():
        raise FileNotFoundError(str(captions_ass))
    output.parent.mkdir(parents=True, exist_ok=True)
    source_has_audio = has_audio(source)

    # Filter graph deliberately uses filter_complex_script when ASS captions are
    # present so literal text cannot become shell arguments.
    top = int(height * 0.085)
    bar = int(height * 0.09)
    fontsize = max(20, round(width / 20))
    video_filters = (
        f"[0:v]split=2[bg][fg];"
        f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
        f"crop={width}:{height},boxblur=20:10[blur];"
        f"[fg]scale={width}:{height}:force_original_aspect_ratio=decrease[front];"
        f"[blur][front]overlay=(W-w)/2:(H-h)/2,"
        f"drawbox=x=0:y={top}:w={width}:h={bar}:color=black@0.65:t=fill,"
        f"drawtext=text='{_drawtext_escape(headline)}':"
        f"fontcolor=white:fontsize={fontsize}:x=(w-text_w)/2:y={top + int(bar*.25)}"
    )
    if captions_ass is not None:
        # Forward slash, colon and quote escaping for FFmpeg filter option paths.
        escaped = str(captions_ass.resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
        video_filters += f",ass=filename='{escaped}'"
    video_filters += "[v]"
    filters = video_filters
    cmd = ["ffmpeg", "-nostdin", "-y", "-v", "error", "-ss", str(start), "-i", str(source)]
    if narration_audio:
        cmd.extend(["-i", str(narration_audio)])
    if narration_audio and source_has_audio:
        filters += ";[0:a]volume=0.18[match];[match][1:a]amix=inputs=2:duration=first:dropout_transition=0[a]"
    elif narration_audio:
        filters += ";[1:a]anull[a]"
    cmd.extend(["-filter_complex", filters, "-map", "[v]"])
    if narration_audio:
        cmd.extend(["-map", "[a]"])
    elif source_has_audio:
        cmd.extend(["-map", "0:a:0"])
    cmd.extend([
        "-t", str(end - start), "-r", "30", "-c:v", "libx264",
        "-preset", "veryfast", "-crf", "24", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-movflags", "+faststart", str(output),
    ])
    subprocess.run(cmd, check=True, timeout=1200)
