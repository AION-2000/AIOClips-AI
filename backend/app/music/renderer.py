"""Low-memory FFmpeg beat editor and MP4 command builder.

Input audio is never altered to evade copyright checks. Rendering uses a single
loudness-normalization pass, 12fps low-resolution working frames and final
upscaling to reduce Render Free memory usage; final pixel dimensions match
the selected preset but fine detail is limited by the internal render size.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

from .beat_editor import scene_boundaries

PRESETS = {
    "shorts": (1080, 1920, 360, 640),
    "youtube": (1920, 1080, 640, 360),
}
COLORS = re.compile(r"^#[0-9a-fA-F]{6}$")


class RenderFailure(RuntimeError):
    pass


def build_ffmpeg_command(
    audio: Path, output: Path, theme: dict,
    sources: dict[int, Path] | None = None, preset: str = "shorts",
    show_visualizer: bool = True, captions: Path | None = None,
) -> list[str]:
    if preset not in PRESETS:
        raise ValueError("Unknown output preset")
    width, height, work_w, work_h = PRESETS[preset]
    scenes = theme.get("scenes", [])
    if not scenes or len(scenes) > 8:
        raise ValueError("Theme needs 1–8 scenes")
    palette = theme.get("palette", [])
    if not isinstance(palette, list) or len(palette) < 2 or not all(
        isinstance(c, str) and COLORS.fullmatch(c) for c in palette
    ):
        raise ValueError("Invalid color palette")
    duration = float(scenes[-1]["end"])
    if not 2 <= duration <= 300:
        raise ValueError("Unsupported video duration")
    for i, scene in enumerate(scenes):
        if (scene["end"] <= scene["start"]
                or i and abs(scene["start"]-scenes[i-1]["end"]) > .01):
            raise ValueError("Scene ranges must be consecutive and increasing")
    sources = sources or {}
    fade = min(.30, min(s["end"]-s["start"] for s in scenes)/5)
    cmd = ["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y",
           "-i", str(audio)]
    graph = []
    for i, scene in enumerate(scenes):
        scene_seconds = scene["end"] - scene["start"]
        length = scene_seconds + (fade if i < len(scenes)-1 else 0)
        if i in sources:
            cmd.extend(["-stream_loop", "-1", "-i", str(sources[i])])
        else:
            base = palette[i % len(palette)].replace("#", "0x")
            accent = palette[(i + 1) % len(palette)].replace("#", "0x")
            gradient = (f"gradients=s={work_w}x{work_h}:r=12:d={length:.3f}:"
                        f"c0={base}:c1={accent}:speed=0.17:"
                        f"type={'radial' if i % 2 else 'linear'}")
            cmd.extend(["-f", "lavfi", "-i", gradient])
        idx = i + 1
        graph.append(
            f"[{idx}:v]fps=12,scale={work_w}:{work_h}:"
            f"force_original_aspect_ratio=increase:flags=fast_bilinear,"
            f"crop={work_w}:{work_h},setsar=1,format=yuv420p,"
            f"trim=duration={length:.3f},setpts=PTS-STARTPTS,"
            f"eq=contrast=1.05:saturation=1.08[v{i}]"
        )
    current = "v0"
    for i in range(1, len(scenes)):
        label = f"joined{i}"
        offset = float(scenes[i]["start"])
        graph.append(f"[{current}][v{i}]xfade=transition=fade:"
                     f"duration={fade:.3f}:offset={offset:.3f}[{label}]")
        current = label
    if show_visualizer:
        graph.append(
            f"[0:a:0]aformat=channel_layouts=mono,"
            f"showwaves=s={int(work_w*.75)}x{max(28,int(work_h*.08))}:"
            f"mode=cline:rate=12:colors=0x66efd6,format=rgba[wave]"
        )
        graph.append(f"[{current}][wave]overlay=x=(W-w)/2:y=H-h-16:"
                     f"shortest=1[visual]")
        current = "visual"
    if captions:
        # Only paths generated in the private job directory are accepted.
        path = captions.resolve().as_posix()
        if any(c in path for c in ("'", ",", ";", "[", "]")):
            raise ValueError("Unsafe captions filename")
        graph.append(f"[{current}]ass=filename='{path}'[captioned]")
        current = "captioned"
    graph.append(
        f"[{current}]scale={width}:{height}:flags=fast_bilinear,"
        f"format=yuv420p[vout]"
    )
    cmd += [
        "-filter_complex_threads", "1",
        "-filter_complex", ";".join(graph),
        "-map", "[vout]", "-map", "0:a:0",
        "-t", f"{duration:.3f}", "-r", "12",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "27",
        "-threads", "2", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k",
        "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
        "-movflags", "+faststart", str(output),
    ]
    return cmd


def render_music(
    audio: Path, output: Path, theme: dict,
    sources: dict[int, Path] | None = None,
    preset: str = "shorts", visualizer: bool = True,
    lyrics: str = "",
) -> Path:
    captions = None
    if lyrics.strip():
        from ..captions import write_animated_captions
        captions = output.with_suffix(".ass")
        duration = float(theme["scenes"][-1]["end"])
        write_animated_captions(lyrics[:1500], duration, captions)
    try:
        command = build_ffmpeg_command(
            audio, output, theme, sources, preset, visualizer, captions
        )
        subprocess.run(command, check=True, capture_output=True, timeout=600)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as exc:
        output.unlink(missing_ok=True)
        raise RenderFailure("FFmpeg rendering failed or exceeded host limits.") from exc
    finally:
        if captions:
            captions.unlink(missing_ok=True)
    if not output.is_file() or output.stat().st_size < 1000:
        raise RenderFailure("FFmpeg produced no usable MP4.")
    return output
