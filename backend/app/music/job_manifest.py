"""Private per-job rights, configuration, progress, provenance and audit manifest."""
from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

RIGHTS = {
    "created_by_me",
    "ai_commercial_plan",
    "commercial_license",
    "royalty_free_commercial",
}
PROOF = re.compile(r"^https://[^/\s]+\.[^\s]+$", re.I)


def validate_rights(kind: str, license_name: str, proof_link: str) -> dict:
    if kind not in RIGHTS:
        raise ValueError("Select a valid commercial-use music rights category.")
    name = license_name.strip()
    link = proof_link.strip()
    if not 3 <= len(name) <= 160:
        raise ValueError("Provide a music license or commercial plan name (3–160 characters).")
    if len(link) > 500 or not PROOF.fullmatch(link):
        raise ValueError("Provide a valid HTTPS license/proof link.")
    return {"category": kind, "license_or_plan": name, "proof_url": link,
            "declared_commercial_use": True}


def write_manifest(folder: Path, data: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    temp = folder / "manifest.json.tmp"
    temp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    os.replace(temp, folder / "manifest.json")


def read_manifest(folder: Path) -> dict:
    return json.loads((folder / "manifest.json").read_text(encoding="utf-8"))


def write_credits(folder: Path, clips: list[dict]) -> None:
    # Store sources for *used* stock clips; generated visuals use no stock source.
    result = {
        "credits": clips, "created_at": time.time(),
        "notice": "Review each source's current license and third-party model/property rights.",
    }
    (folder / "credits.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = ["AIOClips AI — Source credits", ""]
    if not clips:
        lines.append("No third-party stock footage. Visuals generated locally with FFmpeg.")
    for clip in clips:
        lines.extend([
            f"Scene: {clip.get('scene_index', '?')}",
            f"Provider: {clip['provider']}",
            f"Creator: {clip.get('creator', 'Unknown')}",
            f"Source: {clip['source_page']}",
            f"License: {clip['license_url']}",
            "",
        ])
    (folder / "credits.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
