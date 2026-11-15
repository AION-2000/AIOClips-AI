"""Local original football Short production MVP.

Produces a narrated-free, original tactical explainer with FFmpeg drawtext.
No match footage, no automatic publishing, no unlicensed media downloads.
Requires FFmpeg with drawtext support. Input text is authored/reviewed by owner.
"""
from __future__ import annotations
import json
import shutil
import subprocess
import textwrap
from pathlib import Path

def render_explainer(*, title: str, beats: list[str], output: str,
                     seconds_per_beat: int = 5, timeout: int = 180) -> dict:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("FFmpeg is required")
    if not 1 <= len(beats) <= 8 or not 3 <= seconds_per_beat <= 10:
        raise ValueError("Provide 1-8 beats, 3-10 seconds each")
    if not title.strip() or len(title) > 110:
        raise ValueError("Title must be 1-110 characters")
    if any(not b.strip() or len(b) > 180 for b in beats):
        raise ValueError("Each beat must be 1-180 characters")
    target = Path(output).resolve()
    if target.suffix.lower() != ".mp4":
        raise ValueError("Output must be an MP4")
    target.parent.mkdir(parents=True, exist_ok=True)
    # FFmpeg textfile inputs avoid filter injection by user-authored scripts.
    import tempfile
    with tempfile.TemporaryDirectory(prefix="aioclips-") as tmp:
        clips = []
        for idx, beat in enumerate(beats):
            lines = textwrap.wrap(beat, width=23, break_long_words=False)
            if len(lines) > 7:
                raise ValueError("Beat is too long for the vertical layout")
            title_file = Path(tmp) / f"title{idx}.txt"
            beat_file = Path(tmp) / f"beat{idx}.txt"
            title_file.write_text(title, encoding="utf-8")
            beat_file.write_text("\n".join(lines), encoding="utf-8")
            segment = Path(tmp) / f"segment{idx}.mp4"
            # Text files are internal temp paths, never fetched from URLs.
            vf = (
                "drawbox=x=0:y=0:w=iw:h=ih:color=0x071827:t=fill,"
                "drawbox=x=75:y=510:w=930:h=880:color=0x0d5638:t=fill,"
                "drawbox=x=110:y=555:w=860:h=780:color=0x145e42:t=5,"
                "drawbox=x=540:y=555:w=3:h=780:color=white@0.65:t=fill,"
                "drawbox=x=110:y=940:w=860:h=3:color=white@0.65:t=fill,"
                f"drawtext=textfile='{title_file}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=160,"
                f"drawtext=textfile='{beat_file}':fontcolor=white:fontsize=55:line_spacing=20:"
                "x=(w-text_w)/2:y=1460"
            )
            cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
                   "-f", "lavfi", "-i", f"color=c=0x071827:s=1080x1920:r=25:d={seconds_per_beat}",
                   "-vf", vf, "-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p",
                   "-movflags", "+faststart", "-an", str(segment)]
            try:
                subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                raise RuntimeError("FFmpeg failed to render original visuals") from exc
            clips.append(segment)
        manifest = Path(tmp) / "segments.txt"
        manifest.write_text("".join(f"file '{p}'\n" for p in clips), encoding="utf-8")
        cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
               "-f", "concat", "-safe", "0", "-i", str(manifest), "-c", "copy", str(target)]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout)
    return {"output": str(target), "duration_seconds": len(beats) * seconds_per_beat,
            "resolution": "1080x1920", "source": "original generated graphics",
            "publish_approved": False}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate an original, unpublished football explainer MP4")
    parser.add_argument("--title", required=True)
    parser.add_argument("--beat", action="append", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    print(json.dumps(render_explainer(title=args.title, beats=args.beat, output=args.output), indent=2))
