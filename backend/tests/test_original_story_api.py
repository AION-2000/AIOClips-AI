from fastapi.testclient import TestClient
import pytest

from app import server


client = TestClient(server.app)


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    monkeypatch.setenv("STUDIO_ACCESS_TOKEN", "only-test-token")
    monkeypatch.setattr(server, "ROOT", tmp_path)
    server.JOBS.clear()


def headers():
    return {"Authorization": "Bearer only-test-token"}


def story():
    return {
        "reference_url": "https://youtu.be/mmeLCAP74KA?si=abcd",
        "title": "An independently written story",
        "beats": ["A verified event took place", "Here is my personal perspective"],
        "narration_script": None,
        "facts_verified": True,
        "independently_written": True,
        "seconds_per_beat": 3,
    }


def test_original_stories_requires_login():
    assert client.post("/v1/original-stories", json=story()).status_code == 401


def test_original_stories_blocks_unverified_content():
    data = story()
    data["facts_verified"] = False
    assert client.post("/v1/original-stories", headers=headers(), json=data).status_code == 403
    data = story()
    data["independently_written"] = False
    assert client.post("/v1/original-stories", headers=headers(), json=data).status_code == 403


def test_original_stories_rejects_invalid_reference():
    data = story()
    data["reference_url"] = "https://youtube.com.evil.example/watch?v=mmeLCAP74KA"
    assert client.post("/v1/original-stories", headers=headers(), json=data).status_code == 422


def test_original_stories_queue_no_source_video(monkeypatch):
    captured = {}

    def fake_original_render(**kwargs):
        captured.update(kwargs)
        kwargs["output"].write_bytes(b"simulated-original-mp4")
        return kwargs["output"]

    monkeypatch.setattr(server, "render_original_story", fake_original_render)
    result = client.post("/v1/original-stories", headers=headers(), json=story())
    assert result.status_code == 202
    assert result.json()["source"] == "original graphics only"
    job_id = result.json()["job_id"]
    server.JOBS[job_id][0].result(timeout=10)
    assert server.JOBS[job_id][1].read_bytes() == b"simulated-original-mp4"
    assert captured["beats"] == story()["beats"]
    assert "source" not in captured
    assert "reference_url" not in captured


def test_original_stories_no_reference_allowed(monkeypatch):
    data = story()
    data["reference_url"] = None
    monkeypatch.setattr(
        server, "render_original_story",
        lambda **kwargs: kwargs["output"].write_bytes(b"example"),
    )
    result = client.post("/v1/original-stories", headers=headers(), json=data)
    assert result.status_code == 202
    server.JOBS[result.json()["job_id"]][0].result(timeout=10)
