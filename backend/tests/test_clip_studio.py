import shutil
import subprocess

import pytest

from app.captions import write_animated_captions
from app.clip_studio import FootageDeclaration, FootageRights, make_review_clip
from app.match_clips import duration_seconds, has_audio, render_short


def test_rights_evidence_is_required():
    with pytest.raises(ValueError):
        FootageDeclaration(FootageRights.LICENSED, "", True).validate()
    with pytest.raises(ValueError):
        FootageDeclaration(FootageRights.OWNED, "my original recording", False).validate()
    FootageDeclaration(FootageRights.OWNED, "my camera recording", True).validate()


def test_captions_are_animated_and_escaped(tmp_path):
    ass = write_animated_captions(
        "Amazing {goal} scored! 100% real footage.", 9, tmp_path / "captions.ass"
    )
    text = ass.read_text()
    assert "\\kf" in text
    assert "{goal}" not in text
    assert "(goal)" in text
    assert "0:00:09.00" in text
    assert "Style: Big" in text


@pytest.mark.parametrize("duration,script", [
    (0, "text"), (float("nan"), "text"), (3, ""), (3, "  ")
])
def test_invalid_captions(tmp_path, duration, script):
    with pytest.raises(ValueError):
        write_animated_captions(script, duration, tmp_path / "captions.ass")


def test_render_does_not_start_without_rights(tmp_path):
    src = tmp_path / "owned.mp4"
    src.write_bytes(b"irrelevant")
    with pytest.raises(ValueError, match="rights"):
        make_review_clip(
            src, tmp_path / "short.mp4", start=0, end=2,
            rights=FootageDeclaration(FootageRights.OWNED, "me", False),
            headline="TEST", caption_script="Some words"
        )


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg unavailable")
def test_real_captioned_video_with_narration(tmp_path):
    source = tmp_path / "source.mp4"
    narration = tmp_path / "narration.wav"
    output = tmp_path / "clip.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac",
        str(source)
    ], check=True, timeout=30)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=600:sample_rate=16000",
        "-t", "2", str(narration)
    ], check=True, timeout=30)
    make_review_clip(
        source, output, start=0, end=1.5,
        rights=FootageDeclaration(FootageRights.OWNED, "test-generated footage", True),
        headline="EXCITING MOMENT",
        caption_script="What an incredible moment!",
        narration_audio=narration, size=(360, 640),
    )
    assert output.stat().st_size > 1000
    assert has_audio(output)
    assert 1.0 <= duration_seconds(output) <= 2.0


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg unavailable")
def test_render_silent_source_with_narration(tmp_path):
    source = tmp_path / "source.mp4"
    voice = tmp_path / "voice.wav"
    output = tmp_path / "silent-clip.mp4"
    subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=120x120:rate=10",
        "-t", "2", "-c:v", "libx264", str(source)
    ], check=True, timeout=30)
    subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440",
        "-t", "2", str(voice)
    ], check=True, timeout=30)
    assert not has_audio(source)
    render_short(source, output, 0, 1, "YOUR HIGHLIGHT", narration_audio=voice, width=360, height=640)
    assert has_audio(output)
