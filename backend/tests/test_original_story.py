import shutil
import subprocess

import pytest

from app.original_story import render_original_story


def test_invalid_original_script(tmp_path):
    with pytest.raises(ValueError):
        render_original_story(title="", beats=["something happened"], output=tmp_path/"test.mp4")
    with pytest.raises(ValueError):
        render_original_story(title="My story", beats=[], output=tmp_path/"test.mp4")
    with pytest.raises(ValueError):
        render_original_story(title="My story", beats=["This happened"] * 9, output=tmp_path/"test.mp4")
    with pytest.raises(ValueError):
        render_original_story(title="My story", beats=["Good"], output=tmp_path/"test.mov")


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg missing")
def test_original_video_is_generated_from_text_only(tmp_path):
    output = tmp_path / "original.mp4"
    render_original_story(
        title="Incredible World Record", beats=[
            "A remarkable event happened.",
            "Here are the verified facts.",
        ], output=output, seconds_per_beat=3, size=(270, 480),
    )
    assert output.stat().st_size > 2000
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height,duration",
        "-of", "default=noprint_wrappers=1", str(output)
    ], capture_output=True, text=True, check=True, timeout=15)
    assert "width=270" in probe.stdout and "height=480" in probe.stdout


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"), reason="FFmpeg missing")
def test_original_video_accepts_a_narration_track(tmp_path):
    narration = tmp_path/"narration.wav"
    subprocess.run([
        "ffmpeg", "-nostdin", "-v", "error", "-y",
        "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=16000",
        "-t", "1.5", str(narration)
    ], check=True, timeout=15)
    output=tmp_path/"narrated.mp4"
    render_original_story(
        title="Explained", beats=["Here is my original take."], output=output,
        narration_audio=narration, seconds_per_beat=3, size=(270,480)
    )
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "a:0",
        "-show_entries", "stream=codec_type",
        "-of", "default=noprint_wrappers=1", str(output)
    ], capture_output=True, text=True, check=True, timeout=15)
    assert "codec_type=audio" in probe.stdout
