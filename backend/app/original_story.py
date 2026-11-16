"""Create a new narrated, captioned video from independently written content.

No source video is downloaded, cropped, sampled or republished. The caller must
verify factual assertions and avoid copying a third party's script or creative work.
"""
from __future__ import annotations

import math
import re
import subprocess
import tempfile
from pathlib import Path

from .captions import write_animated_captions
from .voice import synthesize_voiceover


def _simple_text(text: str, max_chars: int) -> str:
    if not isinstance(text, str) or not text.strip() or len(text) > max_chars:
        raise ValueError("Missing or overly long original text")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", text):
        raise ValueError("Control characters are not allowed")
    return " ".join(text.split())


def render_original_story(
    *, title: str, beats: list[str], output: Path,
    narration_script: str | None = None,
    seconds_per_beat: int = 5,
    size: tuple[int, int] = (1080, 1920),
    narration_audio: Path | None = None,
) -> Path:
    """Render an original 9:16 graphic story with new artwork and timed captions.

    An AI voice is synthesized if narration_script is given and a prerecorded
    narration_audio path isn't provided. Caption pacing is estimated, not aligned.
    This is a draft, not a legal rights certification or an automatic publisher.
    """
    title = _simple_text(title, 110)
    if not isinstance(beats, list) or not 1 <= len(beats) <= 8:
        raise ValueError("Provide 1-8 original story beats")
    beats = [_simple_text(beat, 180) for beat in beats]
    if not 3 <= seconds_per_beat <= 10:
        raise ValueError("Each story beat must last 3-10 seconds")
    width, height = size
    if width < 240 or height < 420 or width % 2 or height % 2:
        raise ValueError("Invalid portrait dimensions")
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output must be an MP4")
    duration = len(beats) * seconds_per_beat
    if narration_script and narration_audio:
        raise ValueError("Use either a narration script or an existing narration track")
    narration_script = _simple_text(narration_script, 3000) if narration_script else None
    if narration_audio and not narration_audio.is_file():
        raise FileNotFoundError(str(narration_audio))
    output.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="aioclips-original-") as work:
        temporary = Path(work)
        title_path = temporary / "heading.txt"
        title_path.write_text(title, encoding="utf-8")
        beat_paths = []
        import textwrap
        for index, beat in enumerate(beats):
            wrapped = "\n".join(textwrap.wrap(beat, width=26, break_long_words=False))
            path = temporary / f"beat{index}.txt"
            path.write_text(wrapped, encoding="utf-8")
            beat_paths.append(path)
        if narration_script:
            narration_audio = synthesize_voiceover(
                narration_script, temporary / "narration.mp3"
            )
        caption_file = temporary / "captions.ass"
        write_animated_captions(
            narration_script or ". ".join(beats), duration, caption_file
        )

        font_big = max(20, int(width * .050))
        font_body = max(19, int(width * .061))
        # Original abstract geometric background and presentation graphics.
        # Every frame is generated from scratch rather than the reference URL.
        filters = [
            "format=yuv420p",
            f"drawbox=x=0:y=0:w=iw:h=ih:color=0x101b31:t=fill",
            f"drawbox=x={int(width*.04)}:y={int(height*.13)}:w={int(width*.92)}:h={int(height*.007)}:color=0x45eed4:t=fill",
            f"drawbox=x={int(width*.05)}:y={int(height*.31)}:w={int(width*.90)}:h={int(height*.35)}:color=0x233550:t=fill",
            f"drawbox=x={int(width*.05)}:y={int(height*.31)}:w={int(width*.012)}:h={int(height*.35)}:color=0x45eed4:t=fill",
            f"drawtext=textfile='{title_path.as_posix()}':fontcolor=white:fontsize={font_big}:x=(w-text_w)/2:y={int(height*.20)}",
        ]
        for index, beat_path in enumerate(beat_paths):
            start = index * seconds_per_beat
            end = (index + 1) * seconds_per_beat
            filters.append(
                f"drawtext=textfile='{beat_path.as_posix()}':fontcolor=white:"
                f"fontsize={font_body}:line_spacing={int(height*.012)}:"
                f"x=(w-text_w)/2:y={int(height*.40)}:"
                f"enable='between(t,{start},{end-0.001})'"
            )
        # Captions overlay the original visuals; no third-party frames are used.
        filters.append(f"ass=filename='{caption_file.as_posix()}'")

        command = [
            "ffmpeg", "-hide_banner", "-nostdin", "-y", "-v", "error",
            "-f", "lavfi", "-i",
            f"color=c=0x101b31:s={width}x{height}:r=25:d={duration}",
        ]
        if narration_audio:
            command.extend(["-i", str(narration_audio)])
        command.extend(["-vf", ",".join(filters), "-map", "0:v:0"])
        if narration_audio:
            command.extend(["-map", "1:a:0", "-af", "apad", "-c:a", "aac"])
        command.extend([
            "-t", str(duration), "-c:v", "libx264", "-preset", "veryfast",
            "-crf", "25", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
            str(output),
        ])
        subprocess.run(command, check=True, timeout=1200, capture_output=True)
    return output
