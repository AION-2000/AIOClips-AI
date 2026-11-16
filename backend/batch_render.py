"""Render a non-sensitive original story in a GitHub Actions batch job.

Do not use for private scripts or footage in a public repository: workflow inputs
and logs are not a private media storage system.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from app.original_story import render_original_story


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--title", required=True)
    parser.add_argument("--beats-json", required=True)
    parser.add_argument("--seconds-per-beat", type=int, default=5)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    # Never accept a URL, external media path, arbitrary shell commands or secrets.
    title = args.title.strip()
    if not title or len(title) > 110:
        parser.error("Title must be 1-110 characters")
    try:
        beats = json.loads(args.beats_json)
    except json.JSONDecodeError:
        parser.error("Beats must be a JSON array of strings")
    if (not isinstance(beats, list) or not 1 <= len(beats) <= 8
            or any(not isinstance(x, str) or not x.strip() or len(x) > 180 for x in beats)):
        parser.error("Provide 1-8 nonempty story beats, each at most 180 characters")
    if not 3 <= args.seconds_per_beat <= 10:
        parser.error("seconds-per-beat must be between 3 and 10")
    output = Path(args.output).resolve()
    workspace = Path(os.environ.get("GITHUB_WORKSPACE", Path.cwd())).resolve()
    if not output.is_relative_to(workspace / "batch-output") or output.suffix != ".mp4":
        parser.error("Output must be an MP4 under batch-output/")
    output.parent.mkdir(parents=True, exist_ok=True)
    render_original_story(
        title=title, beats=beats, seconds_per_beat=args.seconds_per_beat,
        output=output, narration_script=None,
        size=(540, 960),  # Free runner-friendly draft; 9:16.
    )
    print(f"Rendered {output.name} ({output.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
