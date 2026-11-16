"""Beat-aligned deterministic scene boundaries, independent of the theme provider."""
from __future__ import annotations

import math


def scene_boundaries(duration: float, beats: list[float], count: int = 4) -> list[float]:
    """Return monotonic boundaries including 0 and exact duration.

    Quantize requested evenly-spaced cuts to a nearby beat if that does not
    create a scene shorter than 2 seconds.  Cut tolerance is bounded to 0.7s.
    """
    if not math.isfinite(duration) or not 2 <= duration <= 600:
        raise ValueError("Invalid audio duration")
    count = max(1, min(8, int(count), max(1, int(duration // 3))))
    valid = sorted(set(t for t in beats if math.isfinite(t) and 0 < t < duration))
    boundaries = [0.0]
    for i in range(1, count):
        intended = duration * i / count
        options = [b for b in valid if abs(b - intended) <= .7
                   and b - boundaries[-1] >= 2
                   and duration - b >= 2]
        chosen = min(options, key=lambda b: abs(b-intended)) if options else intended
        if chosen - boundaries[-1] >= 2 and duration - chosen >= 2:
            boundaries.append(round(chosen, 3))
    boundaries.append(round(duration, 3))
    return boundaries


def timed_scenes(duration: float, beats: list[float], keywords: list[str]) -> list[dict]:
    labels = [str(x).strip()[:60] or "abstract light" for x in keywords][:8]
    if not labels:
        labels = ["abstract light"]
    bounds = scene_boundaries(duration, beats, len(labels))
    return [{"start": bounds[i], "end": bounds[i+1],
             "keywords": labels[min(i, len(labels)-1)]}
            for i in range(len(bounds)-1)]
