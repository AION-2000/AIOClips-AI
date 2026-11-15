"""Generate readable, animated ASS captions for vertical clips.

Caption timings are estimates unless supplied by a forced-alignment service.
"""
from __future__ import annotations

import math
import re
from pathlib import Path


def _ass_time(seconds: float) -> str:
    centiseconds = int(round(seconds * 100))
    hours, rem = divmod(centiseconds, 360000)
    minutes, rem = divmod(rem, 6000)
    secs, cs = divmod(rem, 100)
    return f"{hours}:{minutes:02}:{secs:02}.{cs:02}"


def _clean(text: str) -> str:
    # Prevent ASS override injection and preserve plain, legible captions.
    cleaned = text.replace("{", "(").replace("}", ")").replace("\\", "/")
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", cleaned)
    return " ".join(cleaned.split())


def write_animated_captions(
    script: str, duration: float, output: Path, *, words_per_card: int = 4
) -> Path:
    """Create animated, bottom-center caption cards, using estimated pacing.

    For precise synchronization use transcript word timestamps instead of these
    evenly allocated timings. Does not guarantee accuracy for synthesized speech.
    """
    if not math.isfinite(duration) or duration <= 0:
        raise ValueError("Duration must be positive and finite")
    if not 1 <= words_per_card <= 7:
        raise ValueError("words_per_card must be 1 to 7")
    safe_script = _clean(script)
    if not safe_script or len(safe_script) > 3000:
        raise ValueError("Caption script must contain 1-3000 characters")
    words = safe_script.split()
    if len(words) > 400:
        raise ValueError("Too many words for a Short")

    header = """[Script Info]
Title: AIOClips Animated Captions
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 2

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Big,DejaVu Sans,68,&H00FFFFFF,&H0000FFFF,&H00222222,&H90000000,1,0,0,0,100,100,0,0,1,5,2,2,90,90,315,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    # Each word gets a similar share of duration; long words slightly more.
    weights = [max(1.0, min(2.5, len(w) / 5)) for w in words]
    total_weight = sum(weights)
    elapsed = 0.0
    events: list[str] = []
    for start_idx in range(0, len(words), words_per_card):
        current = words[start_idx:start_idx + words_per_card]
        portion = sum(weights[start_idx:start_idx + len(current)])
        span = duration * portion / total_weight
        start = elapsed
        elapsed = min(duration, elapsed + span)
        # Karaoke highlights the currently spoken word with contrast coloring.
        word_weights = weights[start_idx:start_idx + len(current)]
        tags = []
        for word, w in zip(current, word_weights):
            centiseconds = max(1, round(span * 100 * w / portion))
            tags.append("{\\kf" + str(centiseconds) + "}" + word)
        text = "{\\fad(100,100)}" + " ".join(tags)
        events.append(
            f"Dialogue: 0,{_ass_time(start)},{_ass_time(elapsed)},Big,,0,0,0,,{text}"
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(header + "\n".join(events) + "\n", encoding="utf-8")
    return output
