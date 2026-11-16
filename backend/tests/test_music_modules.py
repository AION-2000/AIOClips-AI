"""Music algorithm, licenses, theme parsing, stock and FFmpeg regression tests."""
import json
import shutil
import subprocess
from pathlib import Path

import pytest

from app.music.audio_analyzer import AudioStats, analyze_audio, UnsupportedAudio
from app.music.beat_editor import scene_boundaries, timed_scenes
from app.music.job_manifest import validate_rights, write_credits, write_manifest, read_manifest
from app.music.music_provider import sanitize_generation_prompt, generate_music
from app.music.renderer import build_ffmpeg_command, render_music
from app.music.theme_planner import fallback_theme, parse_theme_json, plan_theme
from app.music.visual_fetcher import search_query, download_stock, StockUnavailable


def stats():
    return AudioStats(duration=12.0, bpm=120, beat_times=[i * 0.5 for i in range(24)],
                      energy_curve=[.2, .4, .8], mean_energy=.42, peak_energy=.8)


def test_rights_gate_and_manifest(tmp_path):
    with pytest.raises(ValueError):
        validate_rights("bad", "my music", "https://example.com/lic")
    with pytest.raises(ValueError):
        validate_rights("created_by_me", "x", "https://example.com/lic")
    with pytest.raises(ValueError):
        validate_rights("commercial_license", "Licensed track", "")
    with pytest.raises(ValueError):
        validate_rights("commercial_license", "Licensed track", "http://example.com/lic")
    rights = validate_rights("commercial_license", "License 2026",
                             "https://example.com/permission")
    assert rights["declared_commercial_use"] is True
    write_manifest(tmp_path, {"rights": rights, "status": "queued"})
    assert read_manifest(tmp_path)["rights"]["proof_url"].startswith("https://")


def test_beats_and_scene_bounds():
    b = scene_boundaries(12, [i * .5 for i in range(24)], 4)
    assert b == [0.0, 3.0, 6.0, 9.0, 12.0]
    assert all(y - x >= 2 for x, y in zip(b, b[1:]))
    s = timed_scenes(12, stats().beat_times, ["sky", "ocean", "city"])
    assert s[0]["start"] == 0 and s[-1]["end"] == 12
    assert all(s[i]["end"] == s[i+1]["start"] for i in range(len(s)-1))


def test_theme_fallback_and_json(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fallback, warning = plan_theme(stats())
    assert fallback["planner"] == "offline-rules" and "missing" in warning
    assert fallback["scenes"][-1]["end"] == 12
    payload = {
        "mood": "wistful", "palette": ["#000022", "#C0A088"],
        "scenes": [{"start": 0, "end": 6, "keywords": "mountain blue"},
                   {"start": 6, "end": 12, "keywords": "stars light"}],
        "title": "Quiet Changes", "description": "An original visual sequence",
    }
    themed = parse_theme_json(json.dumps(payload), stats())
    assert themed["planner"] == "claude-sonnet-5-5"
    assert themed["scenes"][-1]["end"] == 12
    with pytest.raises(ValueError):
        parse_theme_json('{"mood":"dark","palette":[],"scenes":[]}', stats())
    with pytest.raises(ValueError):
        parse_theme_json("not JSON", stats())


def test_stock_queries_credits_and_safe_downloads(tmp_path):
    assert search_query("  neon!! CITY, after  sunset  ") == "neon CITY after sunset"
    write_credits(tmp_path, [{"scene_index": 1, "provider": "Pexels",
        "creator": "Example Artist", "source_page": "https://www.pexels.com/video/example",
        "license_url": "https://www.pexels.com/license/"}])
    assert (tmp_path / "credits.json").exists()
    text = (tmp_path / "credits.txt").read_text()
    assert "Pexels" in text and "Example Artist" in text
    write_credits(tmp_path, [])
    assert "No third-party stock footage" in (tmp_path / "credits.txt").read_text()
    with pytest.raises(StockUnavailable):
        download_stock("http://127.0.0.1/file.mp4", tmp_path / "bad.mp4", client=None)


def test_provider_fails_closed_for_imitations():
    with pytest.raises(ValueError):
        sanitize_generation_prompt("Make it sound like a famous performer")
    with pytest.raises(ValueError):
        sanitize_generation_prompt("Taylor Swift pop song")
    assert sanitize_generation_prompt("Bright slow jazz ambient") == "bright slow jazz ambient"
    with pytest.raises(RuntimeError):
        generate_music("some-fake-provider", "Bright slow jazz ambient", "/tmp/out.mp3")


def test_ffmpeg_builder_dimensions_filters_and_safety(tmp_path):
    theme = fallback_theme(stats())
    command = build_ffmpeg_command(tmp_path / "input.wav", tmp_path / "out.mp4", theme,
                                   preset="shorts", show_visualizer=True)
    joined = " ".join(command)
    assert "xfade" in joined and "showwaves" in joined
    assert "scale=1080:1920" in joined and "loudnorm" in joined
    landscape = " ".join(build_ffmpeg_command(
        tmp_path / "input.wav", tmp_path / "out.mp4", theme,
        preset="youtube", show_visualizer=False))
    assert "scale=1920:1080" in landscape
    assert "showwaves" not in landscape
    with pytest.raises(ValueError):
        build_ffmpeg_command(tmp_path / "a.wav", tmp_path / "out.mp4", theme,
                             preset="unsupported")


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg missing")
def test_actual_music_audio_analysis_and_mp4(tmp_path):
    sound = tmp_path / "licensed_synthetic.wav"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi",
         "-i", "sine=frequency=440:duration=4", "-ar", "16000", str(sound)],
        check=True, timeout=20, capture_output=True,
    )
    analyzed = analyze_audio(sound, 15)
    assert 3.8 <= analyzed.duration <= 4.2
    assert 60 <= analyzed.bpm <= 200
    assert analyzed.energy_curve
    with pytest.raises(UnsupportedAudio):
        analyze_audio(sound, 3)
    theme = fallback_theme(analyzed)
    output = tmp_path / "out.mp4"
    render_music(sound, output, theme, preset="shorts", visualizer=True)
    assert output.stat().st_size > 3000
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(output)],
        text=True, capture_output=True, check=True, timeout=10,
    )
    assert "1080,1920" in probe.stdout
