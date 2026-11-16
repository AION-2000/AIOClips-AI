"""Music upload rights gate, auth, manifest, credits and video access."""
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app import original_api
from app.music import api as music
from app.music.job_manifest import read_manifest, write_credits, write_manifest

TOKEN = "test-secret-for-music-access-1234567890"
HEADERS = {"Authorization": "Bearer " + TOKEN}
client = TestClient(original_api.app)


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_ACCESS_TOKEN", TOKEN)
    monkeypatch.setattr(music, "MUSIC_ROOT", tmp_path)
    with music.LOCK:
        music.MUSIC_JOBS.clear()
    with original_api.LOCK:
        original_api.REQUESTS.clear()
    yield
    with music.LOCK:
        for future in music.MUSIC_JOBS.values():
            future.result(timeout=90)
        music.MUSIC_JOBS.clear()


def synth_wav(tmp_path):
    sound = tmp_path / "synthetic.wav"
    subprocess.run(
        ["ffmpeg", "-nostdin", "-v", "error", "-y", "-f", "lavfi",
         "-i", "sine=frequency=600:duration=3", "-ar", "16000", str(sound)],
        check=True, capture_output=True, timeout=20,
    )
    return sound.read_bytes()


def request_args(audio, *, confirmed="true"):
    return {
        "headers": HEADERS,
        "data": {
            "rights": "created_by_me",
            "license_name": "Recorded in my studio",
            "proof_link": "https://example.com/my-audio-rights",
            "rights_confirmed": confirmed,
            "preset": "shorts", "prefer_ai": "false",
            "prefer_stock": "false",
        },
        "files": {"audio": ("sound.wav", audio, "audio/wav")},
    }


def test_music_routes_require_owner_and_gate(tmp_path):
    args = request_args(b"test")
    assert client.post("/v1/music/jobs", data=args["data"], files=args["files"]).status_code == 401
    args = request_args(b"test", confirmed="false")
    assert client.post("/v1/music/jobs", **args).status_code == 403
    args = request_args(b"test")
    args["data"].pop("proof_link")
    assert client.post("/v1/music/jobs", **args).status_code == 422
    args = request_args(b"test")
    args["data"]["rights"] = "unverified"
    assert client.post("/v1/music/jobs", **args).status_code == 422
    args = request_args(b"test")
    args["files"] = {"audio": ("evil.bin", b"bad", "application/octet-stream")}
    assert client.post("/v1/music/jobs", **args).status_code == 415
    assert not any(tmp_path.iterdir())


def test_generation_providers_disabled():
    data = client.get("/v1/music/config", headers=HEADERS)
    assert data.status_code == 200
    assert data.json()["music_generation_providers"] == []
    assert data.json()["retention_hours"] == 24
    assert client.post("/v1/music/generate", headers=HEADERS).status_code == 501


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg required")
def test_real_music_upload_status_manifest_credits_download(tmp_path):
    data = synth_wav(tmp_path)
    response = client.post("/v1/music/jobs", **request_args(data))
    assert response.status_code == 202, response.text
    job_id = response.json()["job_id"]
    assert len(job_id) == 32
    manifest = client.get(f"/v1/music/jobs/{job_id}/manifest", headers=HEADERS)
    assert manifest.status_code == 200
    assert manifest.json()["rights"]["category"] == "created_by_me"
    assert manifest.json()["rights"]["proof_url"].startswith("https://")
    assert client.get(f"/v1/music/jobs/{job_id}/download").status_code == 401
    music.MUSIC_JOBS[job_id].result(timeout=120)
    status = client.get(f"/v1/music/jobs/{job_id}", headers=HEADERS)
    assert status.status_code == 200
    assert status.json()["status"] == "ready", status.json()
    assert "title" in status.json()
    assert "description" in status.json()
    assert status.json()["stats"]["duration"] >= 2.9
    preview = client.get(f"/v1/music/jobs/{job_id}/download", headers=HEADERS)
    assert preview.status_code == 200
    assert preview.content.startswith(b"\x00\x00\x00")
    credits = client.get(f"/v1/music/jobs/{job_id}/credits", headers=HEADERS)
    assert credits.status_code == 200
    assert "No third-party stock" in credits.text
    assert (tmp_path / job_id / "video.mp4").stat().st_size > 2000


def test_music_expiry(monkeypatch, tmp_path):
    folder = tmp_path / ("a"*32)
    folder.mkdir()
    write_manifest(folder, {"status": "ready"})
    import os, time
    past = time.time() - music.MUSIC_TTL_SECONDS - 60
    os.utime(folder, (past, past))
    music.cleanup_music_jobs()
    assert not folder.exists()
