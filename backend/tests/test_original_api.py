"""Security, job lifecycle and actual FFmpeg tests for the mobile original-story API."""
import os
import shutil
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from app import original_api as api


TOKEN = "test-owner-token-that-is-long-enough-12345678"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}
STORY = {
    "title": "My original short",
    "beats": ["Here is a verified, independently written idea."],
    "seconds_per_beat": 3,
    "facts_verified": True,
    "independently_written": True,
}


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_ACCESS_TOKEN", TOKEN)
    monkeypatch.setattr(api, "DATA_DIR", tmp_path)
    with api.LOCK:
        api.JOBS.clear()
        api.REQUESTS.clear()
    yield
    with api.LOCK:
        for job in api.JOBS.values():
            job.future.result(timeout=40)
        api.JOBS.clear()
        api.REQUESTS.clear()


client = TestClient(api.app)


def test_health_and_auth():
    assert client.get("/v1/health").json()["status"] == "ok"
    assert client.post("/v1/story/jobs", json=STORY).status_code == 401
    assert client.post("/v1/story/jobs", json=STORY, headers={"Authorization": "Bearer wrong"}).status_code == 401
    with api.LOCK:
        api.REQUESTS.clear()
    assert client.get("/v1/story/jobs/" + "a" * 32, headers=HEADERS).status_code == 404


def test_missing_server_secret_is_closed(monkeypatch):
    monkeypatch.delenv("STUDIO_ACCESS_TOKEN")
    assert client.post("/v1/story/jobs", headers=HEADERS, json=STORY).status_code == 503


def test_exact_origin_preflight():
    good = client.options(
        "/v1/story/jobs",
        headers={"Origin": api.ORIGIN, "Access-Control-Request-Method": "POST",
                 "Access-Control-Request-Headers": "authorization,content-type"},
    )
    assert good.status_code == 200
    assert good.headers["access-control-allow-origin"] == api.ORIGIN
    bad = client.options(
        "/v1/story/jobs",
        headers={"Origin": "https://attacker.example", "Access-Control-Request-Method": "POST"},
    )
    assert "access-control-allow-origin" not in bad.headers
    assert client.get("/v1/health").headers["cache-control"] == "no-store"


@pytest.mark.parametrize("updates", [
    {"beats": []},
    {"beats": ["one"] * 9},
    {"beats": [" "]},
    {"beats": ["X" * 181]},
    {"title": "  "},
    {"title": "X" * 111},
    {"title": "bad\nscript"},
    {"seconds_per_beat": 2},
    {"seconds_per_beat": 11},
    {"unrecognized_setting": "x"},
])
def test_bad_story_is_rejected(updates):
    assert client.post("/v1/story/jobs", headers=HEADERS,
                       json={**STORY, **updates}).status_code == 422


def test_copyright_confirmations_required():
    assert client.post(
        "/v1/story/jobs", headers=HEADERS,
        json={**STORY, "independently_written": False},
    ).status_code == 403


def test_job_progress_download_and_cleanup(monkeypatch, tmp_path):
    def fake_render(**kwargs):
        kwargs["output"].write_bytes(b"generated-mp4")
    monkeypatch.setattr(api, "render_original_story", fake_render)
    response = client.post("/v1/story/jobs", headers=HEADERS, json=STORY)
    assert response.status_code == 202, response.text
    assert response.json()["resolution"] == "540x960"
    job_id = response.json()["job_id"]
    api.JOBS[job_id].future.result(timeout=10)
    status = client.get("/v1/story/jobs/" + job_id, headers=HEADERS)
    assert status.json()["status"] == "ready"
    assert client.get("/v1/story/jobs/" + job_id + "/download").status_code == 401
    file = client.get("/v1/story/jobs/" + job_id + "/download", headers=HEADERS)
    assert file.content == b"generated-mp4"
    assert file.headers["content-type"].startswith("video/mp4")
    api.JOBS[job_id].created_at = time.time() - api.TTL_SECONDS - 10
    api.cleanup_expired()
    assert not list(tmp_path.glob("*.mp4"))
    assert client.get("/v1/story/jobs/" + job_id, headers=HEADERS).status_code == 404


def test_submission_is_rate_limited(monkeypatch):
    def fake_render(**kwargs):
        kwargs["output"].write_bytes(b"generated")
    monkeypatch.setattr(api, "render_original_story", fake_render)
    codes = [client.post("/v1/story/jobs", headers=HEADERS, json=STORY).status_code
             for _ in range(6)]
    assert codes[:5] == [202] * 5
    assert codes[-1] == 429


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg/ffprobe not installed")
def test_end_to_end_real_mp4():
    response = client.post("/v1/story/jobs", headers=HEADERS, json=STORY)
    assert response.status_code == 202, response.text
    job_id = response.json()["job_id"]
    api.JOBS[job_id].future.result(timeout=120)
    download = client.get("/v1/story/jobs/" + job_id + "/download", headers=HEADERS)
    assert download.status_code == 200
    assert len(download.content) > 2500
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height",
         "-of", "default=noprint_wrappers=1",
         str(api.JOBS[job_id].output)],
        text=True, capture_output=True, check=True, timeout=20,
    )
    assert "width=540" in probe.stdout
    assert "height=960" in probe.stdout
