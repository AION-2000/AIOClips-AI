"""Commercial-use-safe music generation plugin boundary.

No provider is registered by default. A free-tier price does not mean its music
may legally be published commercially. Do NOT pass real artist names to a
future provider or guess at terms; verify and record the actual license first.
"""
from __future__ import annotations

import re
from typing import Protocol


class MusicGenerationProvider(Protocol):
    name: str
    commercial_license_url: str

    def generate(self, prompt: str, destination: str) -> str:
        """Return a locally generated audio filename on successful generation."""
        ...


PROVIDERS: dict[str, MusicGenerationProvider] = {}


def sanitize_generation_prompt(prompt: str) -> str:
    if not isinstance(prompt, str) or not 3 <= len(prompt.strip()) <= 300:
        raise ValueError("Music prompt must be 3–300 characters.")
    # Prohibit requests to mimic performers; cannot infer every real-world name.
    if re.search(r"\b(?:in (?:the )?style of|sound(?:s)? like|sing like|imitat(?:e|ing)|"
                 r"copy|as performed by|similar to|like the artist)\b",
                 prompt, flags=re.I):
        raise ValueError("Artist imitation requests are not accepted.")
    if re.search(r"[\x00-\x1f\x7f]", prompt):
        raise ValueError("Invalid music prompt.")
    return prompt.strip()


def available_providers() -> list[dict]:
    return [{"name": p.name, "commercial_license_url": p.commercial_license_url}
            for p in PROVIDERS.values()]


def generate_music(provider: str, prompt: str, destination: str) -> str:
    safe_prompt = sanitize_generation_prompt(prompt)
    if provider not in PROVIDERS:
        raise RuntimeError(
            "No AI music generator with verified free commercial-use rights is configured. "
            "Upload commercially licensed audio instead."
        )
    return PROVIDERS[provider].generate(safe_prompt, destination)
