"""FFmpeg-backed low-memory audio analysis (no paid services).

RMS energy and onset autocorrelation estimate tempo; they do not guarantee
musically correct downbeats. Decode only the bounded uploaded duration.
"""
from __future__ import annotations

import array
import json
import math
import os
import statistics
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


class UnsupportedAudio(ValueError):
    pass


@dataclass(frozen=True)
class AudioStats:
    duration: float
    bpm: float
    beat_times: list[float]
    energy_curve: list[float]
    mean_energy: float
    peak_energy: float

    def as_dict(self) -> dict:
        return {
            "duration": self.duration, "bpm": self.bpm,
            "beat_times": self.beat_times, "energy_curve": self.energy_curve,
            "mean_energy": self.mean_energy, "peak_energy": self.peak_energy,
        }


def duration_and_codec(path: Path) -> float:
    try:
        raw = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration:stream=codec_type,codec_name", "-of", "json", str(path)],
            capture_output=True, check=True, timeout=20,
        )
        data = json.loads(raw.stdout)
        audio = [s for s in data.get("streams", []) if s.get("codec_type") == "audio"]
        duration = float(data.get("format", {}).get("duration", 0))
        if not audio or not math.isfinite(duration) or duration < 2:
            raise UnsupportedAudio("An audio track of at least 2 seconds is required.")
        return duration
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, ValueError,
            KeyError, TypeError, json.JSONDecodeError) as exc:
        raise UnsupportedAudio("Unsupported or unreadable audio; use MP3, WAV or M4A.") from exc


def analyze_audio(path: Path, max_seconds: int = 120) -> AudioStats:
    duration = duration_and_codec(path)
    if duration > max_seconds + 0.1:
        raise UnsupportedAudio(f"Track exceeds configured {max_seconds}-second limit.")
    sample_rate = 8000
    # 100ms frames, allowing energy analysis without scipy/librosa memory cost.
    cmd = ["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
           "-map", "0:a:0", "-t", f"{duration:.3f}",
           "-ac", "1", "-ar", str(sample_rate), "-f", "s16le", "-"]
    try:
        proc = subprocess.run(cmd, capture_output=True, check=True, timeout=90)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
        raise UnsupportedAudio("FFmpeg could not decode this audio track.") from exc
    samples = array.array("h")
    samples.frombytes(proc.stdout[:len(proc.stdout) // 2 * 2])
    if sys.byteorder != "little":
        samples.byteswap()
    if not samples:
        raise UnsupportedAudio("Audio contains no decodable samples.")
    frame = 800
    energy = []
    for offset in range(0, len(samples), frame):
        block = samples[offset:offset + frame]
        if not block:
            continue
        energy.append(math.sqrt(sum(s*s for s in block) / len(block)) / 32768)
    if len(energy) < 10:
        raise UnsupportedAudio("Audio track is too short to analyze.")
    maximum = max(energy) or 1.0
    normalized = [e / maximum for e in energy]
    novelty = [0.0] + [max(0.0, normalized[i] - normalized[i - 1])
                       for i in range(1, len(normalized))]
    # Tempo grid 60–180 BPM, scoring an onset autocorrelation at 10 Hz.
    scores = []
    for lag in range(3, 11):
        score = sum(novelty[i] * novelty[i - lag] for i in range(lag, len(novelty)))
        count = max(1, len(novelty) - lag)
        scores.append((score / count, lag))
    best, lag = max(scores)
    bpm = round(min(180.0, max(60.0, 60.0 / (lag / 10.0))), 1) if best > 0.00004 else 120.0
    interval = 60 / bpm
    strongest = max(range(min(len(novelty), max(1, round(interval * 10)))),
                    key=novelty.__getitem__)
    phase = strongest / 10
    beat_times = []
    t = phase
    while t < duration:
        beat_times.append(round(t, 3))
        t += interval
    if not beat_times or beat_times[0] > 0.3:
        beat_times.insert(0, 0.0)
    buckets = []
    for i in range(0, len(normalized), 10):
        buckets.append(round(statistics.fmean(normalized[i:i+10]), 3))
    return AudioStats(
        duration=round(duration, 3), bpm=bpm, beat_times=beat_times[:1000],
        energy_curve=buckets[:max_seconds+1],
        mean_energy=round(statistics.fmean(normalized), 3),
        peak_energy=round(max(energy), 4),
    )
