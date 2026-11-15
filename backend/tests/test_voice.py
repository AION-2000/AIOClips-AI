import pytest

from app.voice import synthesize_voiceover


def test_voice_requires_server_key(tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        synthesize_voiceover("This is a moment!", tmp_path / "voice.mp3")


def test_voice_rejects_invalid_input(tmp_path):
    with pytest.raises(ValueError):
        synthesize_voiceover("", tmp_path / "voice.mp3", api_key="test")
    with pytest.raises(ValueError):
        synthesize_voiceover("Hello", tmp_path / "voice.mp3", api_key="test", voice="unknown")


def test_voice_request_and_audio_output(tmp_path, monkeypatch):
    captured = {}

    class FakeResponse:
        headers = {"Content-Type": "audio/mpeg"}
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def read(self, count):
            return b"fake-test-mp3"

    def fake_urlopen(req, timeout):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["timeout"] = timeout
        assert req.get_header("Authorization") == "Bearer test-private-key"
        return FakeResponse()

    monkeypatch.setattr("app.voice.urllib.request.urlopen", fake_urlopen)
    output = synthesize_voiceover(
        "That was amazing!", tmp_path / "voice.mp3", api_key="test-private-key"
    )
    assert output.read_bytes() == b"fake-test-mp3"
    assert captured["url"] == "https://api.openai.com/v1/audio/speech"
    assert captured["method"] == "POST"
