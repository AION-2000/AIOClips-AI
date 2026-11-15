import io
import shutil
import subprocess

import pytest
from fastapi.testclient import TestClient

from app import server
from app.match_clips import Moment

client = TestClient(server.app)


@pytest.fixture(autouse=True)
def isolate_studio(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_ACCESS_TOKEN", "test-access-token")
    monkeypatch.setattr(server, "ROOT", tmp_path)
    server.JOBS.clear()


def authorization():
    return {"Authorization": "Bearer test-access-token"}


def test_web_studio_is_served():
    page = client.get("/")
    assert page.status_code == 200
    assert "AIOClips" in page.text
    script = client.get("/studio.js")
    assert script.status_code == 200
    assert 'request(' in script.text


def test_private_endpoints_require_token():
    assert client.post("/v1/links", json={"url": "https://youtu.be/mmeLCAP74KA"}).status_code == 401
    assert client.post("/v1/links", headers={"Authorization": "Bearer wrong"}, json={}).status_code == 401


def test_youtube_url_is_recognized_not_downloaded():
    response = client.post(
        "/v1/links", headers=authorization(),
        json={"url": "https://youtu.be/mmeLCAP74KA?si=abc"},
    )
    assert response.status_code == 200
    assert response.json()["importable"] is False


def test_invalid_video_is_rejected_and_removed(tmp_path):
    response = client.post(
        "/v1/uploads", headers=authorization(),
        files={"video": ("bad.mp4", b"not-a-video", "video/mp4")},
    )
    assert response.status_code == 415
    assert list((tmp_path / "uploads").glob("*")) == []


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="FFmpeg unavailable")
def test_real_upload_moments_and_render(tmp_path, monkeypatch):
    source = tmp_path / "generated.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-hide_banner", "-v", "error",
        "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=500:sample_rate=16000",
        "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", str(source)
    ], check=True, timeout=30)
    with source.open("rb") as file:
        uploaded = client.post(
            "/v1/uploads", headers=authorization(),
            files={"video": ("owned.mp4", file, "video/mp4")},
        )
    assert uploaded.status_code == 200
    asset_id = uploaded.json()["asset_id"]
    monkeypatch.setattr(server, "suggest_video_moments", lambda *a, **k: [
        Moment(0, 1, 0.9)
    ])
    result = client.post(
        "/v1/moments", headers=authorization(), json={"asset_id": asset_id, "limit": 1}
    )
    assert result.status_code == 200
    assert result.json()["moments"][0]["kind"] == "high_energy"

    payload = {
        "asset_id": asset_id, "start": 0, "end": 1,
        "headline": "AWESOME MOMENT", "caption_script": "A truly great moment",
        "rights": "owned", "rights_evidence": "my generated test video",
        "permission_to_publish": False,
    }
    denied = client.post("/v1/renders", headers=authorization(), json=payload)
    assert denied.status_code == 403
    assert client.get("/v1/exports/" + ("a" * 32), headers=authorization()).status_code == 404

    # A single test export confirms the API wires to FFmpeg, not a mock dashboard.
    monkeypatch.setattr(server, "make_review_clip",
                        lambda s, out, **kwargs: out.parent.mkdir(exist_ok=True) or out.write_bytes(b"test-mp4"))
    payload["permission_to_publish"] = True
    created = client.post("/v1/renders", headers=authorization(), json=payload)
    assert created.status_code == 202
    job_id = created.json()["job_id"]
    server.JOBS[job_id][0].result(timeout=10)
    assert client.get("/v1/renders/" + job_id, headers=authorization()).json()["status"] == "ready"
    assert client.get("/v1/exports/" + job_id, headers=authorization()).status_code == 200
