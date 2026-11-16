"""Input validation checks for the manual original-story batch renderer."""
import json
import sys
from pathlib import Path

import pytest

from batch_render import main


def test_rejects_invalid_json(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [
        "batch_render.py", "--title", "Test", "--beats-json", "not-json",
        "--output", str(tmp_path / "batch-output" / "out.mp4"),
    ])
    with pytest.raises(SystemExit):
        main()


def test_rejects_output_outside_batch_directory(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [
        "batch_render.py", "--title", "Test", "--beats-json", json.dumps(["One beat"]),
        "--output", str(tmp_path / "private.mp4"),
    ])
    with pytest.raises(SystemExit):
        main()


def test_rejects_non_string_beats(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setattr(sys, "argv", [
        "batch_render.py", "--title", "Test", "--beats-json", '[123]',
        "--output", str(tmp_path / "batch-output" / "out.mp4"),
    ])
    with pytest.raises(SystemExit):
        main()
