"""Hosted rights-authorized upload → highlight → actual FFmpeg clip API tests."""
import shutil
import subprocess
import time

import pytest
from fastapi.testclient import TestClient

from app import original_api as api


TOKEN = "synthetic-owner-token-for-test-only-123456789"
HEADERS = {"Authorization": "Bearer " + TOKEN}
client = TestClient(api.app)


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_ACCESS_TOKEN", TOKEN)
    monkeypatch.setattr(api, "DATA_DIR", tmp_path)
    with api.LOCK:
        api.JOBS.clear()
        api.UPLOADED.clear()
        api.REQUESTS.clear()
    yield
    with api.LOCK:
        for job in api.JOBS.values():
            job.future.result(timeout=120)
        api.JOBS.clear()
        api.UPLOADED.clear()
        api.REQUESTS.clear()


def upload_bytes(payload=b"invalid footage", *, evidence="Original creator granted permission"):
    return {
        "headers": HEADERS,
        "data": {
            "rights": "licensed", "rights_evidence": evidence,
            "permission_to_edit": "true",
        },
        "files": {"video": ("authorized.mp4", payload, "video/mp4")},
    }


def test_upload_requires_authorization_and_rights():
    args = upload_bytes()
    args.pop("headers")
    assert client.post("/v1/footage/uploads", **args).status_code == 401
    args = upload_bytes()
    args["data"]["permission_to_edit"] = "false"
    assert client.post("/v1/footage/uploads", **args).status_code == 403
    args = upload_bytes()
    args["data"]["rights_evidence"] = ""
    assert client.post("/v1/footage/uploads", **args).status_code == 422
    args = upload_bytes()
    args["files"] = {"video": ("x.txt", b"bad", "text/plain")}
    assert client.post("/v1/footage/uploads", **args).status_code == 415


def test_unplayable_video_is_rejected_and_removed(tmp_path):
    result = client.post("/v1/footage/uploads", **upload_bytes())
    assert result.status_code == 415
    assert list((tmp_path / "uploads").glob("*")) == []


def test_clip_rejects_nonexistent_asset():
    result = client.post(
        "/v1/footage/" + "a" * 32 + "/clips",
        headers=HEADERS,
        json={"start": 0, "end": 2, "headline": "Example",
              "caption_script": "My own commentary", "permission_to_publish": True},
    )
    assert result.status_code == 404


@pytest.mark.skipif(not shutil.which("ffmpeg") or not shutil.which("ffprobe"),
                    reason="FFmpeg and FFprobe required")
def test_real_licensed_upload_to_vertical_clip(tmp_path):
    source = tmp_path / "owned-licensed-synthetic.mp4"
    subprocess.run([
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=160x90:rate=12",
        "-f", "lavfi", "-i", "sine=frequency=480:sample_rate=16000",
        "-t", "2", "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", str(source),
    ], check=True, capture_output=True, timeout=40)
    response = client.post(
        "/v1/footage/uploads", **upload_bytes(source.read_bytes())
    )
    assert response.status_code == 201, response.text
    asset_id = response.json()["asset_id"]
    assert response.json()["duration"] > 1.5
    assert client.post(
        f"/v1/footage/{asset_id}/highlights", headers=HEADERS,
        json={"seconds": 1.2, "limit": 3},
    ).status_code == 200

    body = {
        "start": 0, "end": 1.2, "headline": "GREAT MOMENT",
        "caption_script": "This is my original review of the moment.",
        "permission_to_publish": True,
    }
    assert client.post(
        f"/v1/footage/{asset_id}/clips", headers=HEADERS,
        json={**body, "permission_to_publish": False},
    ).status_code == 403
    invalid = client.post(
        f"/v1/footage/{asset_id}/clips", headers=HEADERS,
        json={**body, "end": 999},
    )
    assert invalid.status_code == 422
    queued = client.post(
        f"/v1/footage/{asset_id}/clips", headers=HEADERS, json=body,
    )
    assert queued.status_code == 202, queued.text
    job_id = queued.json()["job_id"]
    assert queued.json()["resolution"] == "540x960"
    api.JOBS[job_id].future.result(timeout=120)
    progress = client.get(f"/v1/story/jobs/{job_id}", headers=HEADERS)
    assert progress.json()["status"] == "ready"
    assert client.get(f"/v1/story/jobs/{job_id}/download").status_code == 401
    result = client.get(f"/v1/story/jobs/{job_id}/download", headers=HEADERS)
    assert result.status_code == 200
    assert len(result.content) > 3000
    probe = subprocess.run([
        "ffprobe", "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=width,height",
        "-of", "default=noprint_wrappers=1", str(api.JOBS[job_id].output),
    ], text=True, capture_output=True, check=True, timeout=20)
    assert "width=540" in probe.stdout
    assert "height=960" in probe.stdout

    # Expiry deletes the private upload as well as completed export.
    with api.LOCK:
        api.UPLOADED[asset_id].created_at = time.time() - api.TTL_SECONDS - 10
        api.JOBS[job_id].created_at = time.time() - api.TTL_SECONDS - 10
    api.cleanup_expired()
    assert not api.UPLOADED
    assert not api.JOBS
    assert not (tmp_path / "uploads" / (asset_id + ".media")).exists()
    assert not (tmp_path / (job_id + ".mp4")).exists()
