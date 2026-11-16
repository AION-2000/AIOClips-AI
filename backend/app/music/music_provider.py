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


# Only this restricted set of *generic* descriptors may reach a future
# music-generation provider. Proper names, arbitrary words and artist requests
# are rejected rather than guessed at by an unreliable named-entity filter.
GENERIC_DESCRIPTORS = frozenset("""
ambient acoustic upbeat energetic mellow atmospheric instrumental cinematic
gentle soft intense fast slow relaxing dramatic rhythmic dreamy
electronic classical orchestral jazz blues folk rock pop dance
piano guitar violin cello drums percussion synthesizer synth strings bass
melodic minimal lush warm dark bright peaceful joyful emotional
meditative instrumental downtempo uptempo playful reflective mysterious
calm powerful flowing textures pads arpeggios groove beat
""".split())


def sanitize_generation_prompt(prompt: str) -> str:
    if not isinstance(prompt, str) or not 3 <= len(prompt.strip()) <= 300:
        raise ValueError("Music prompt must be 3–300 characters.")
    if re.search(r"[\x00-\x1f\x7f]", prompt):
        raise ValueError("Invalid music prompt.")
    words = re.findall(r"[A-Za-z]+", prompt.lower())
    if len(words) < 2 or len(words) > 32 or any(
        word not in GENERIC_DESCRIPTORS for word in words
    ):
        raise ValueError(
            "Use only generic mood, genre and instrument descriptors. "
            "Real artist names and imitation prompts are not accepted."
        )
    return " ".join(words)


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
