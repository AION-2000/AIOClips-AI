"""Optional AI voice synthesis. API key stays in the server environment."""
from __future__ import annotations

import json
import os
import urllib.request
from pathlib import Path

_ALLOWED_VOICES = {"alloy", "ash", "ballad", "coral", "echo", "sage", "shimmer", "verse", "marin", "cedar"}
_MAX_AUDIO_BYTES = 25 * 1024 * 1024


def synthesize_voiceover(
    script: str,
    output: Path,
    *,
    voice: str = "marin",
    api_key: str | None = None,
) -> Path:
    """Create an MP3 AI narration with OpenAI's speech endpoint.

    Requires an API account with available credits and server-side OPENAI_API_KEY.
    This does NOT clear rights to an underlying video or guarantee monetization.
    """
    if not isinstance(script, str) or not 1 <= len(script.strip()) <= 4000:
        raise ValueError("Narration must be 1-4000 characters")
    if voice not in _ALLOWED_VOICES:
        raise ValueError("Unsupported narration voice")
    token = api_key if api_key is not None else os.environ.get("OPENAI_API_KEY", "")
    if not token:
        raise RuntimeError("OPENAI_API_KEY must be configured on the server")
    payload = json.dumps({
        "model": "gpt-4o-mini-tts",
        "voice": voice,
        "input": script,
        "instructions": "Narrate clearly, energetically and naturally, with short pauses. Do not impersonate a real person.",
        "response_format": "mp3",
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/audio/speech", data=payload,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "audio/mpeg",
        }, method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as response:
        body = response.read(_MAX_AUDIO_BYTES + 1)
        if not body or len(body) > _MAX_AUDIO_BYTES:
            raise RuntimeError("Invalid or oversized voice response")
        if "audio" not in response.headers.get("Content-Type", "").lower():
            raise RuntimeError("Voice service did not return audio")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(body)
    return output
