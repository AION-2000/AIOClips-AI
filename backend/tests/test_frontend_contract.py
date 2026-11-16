"""Static GitHub Pages UI contract tests (no token or private media needed)."""
from html.parser import HTMLParser
from pathlib import Path
import re
import shutil
import subprocess

import pytest

PAGE = Path(__file__).resolve().parents[2] / "index.html"


class Controls(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.tabs = []
        self.scripts = []

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if "id" in props:
            self.ids.add(props["id"])
        if tag == "button" and "data-tab" in props:
            self.tabs.append(props["data-tab"])


def test_mobile_controls_exist():
    markup = PAGE.read_text(encoding="utf-8")
    parser = Controls()
    parser.feed(markup)
    assert {"story", "reference", "upload"} <= set(parser.tabs)
    required = {
        "storyForm", "storyTitle", "beats", "duration", "facts", "original",
        "ownerToken", "apiUrl", "connect", "generate", "player", "download",
        "jobStatus", "appMessage", "referenceForm", "referenceUrl",
    }
    assert required <= parser.ids
    assert 'name="viewport"' in markup
    assert 'type="password"' in markup
    assert "Needs connected service" in markup or "needs connected service" in markup


@pytest.mark.skipif(not shutil.which("node"), reason="Node.js unavailable")
def test_embedded_javascript_syntax(tmp_path):
    markup = PAGE.read_text(encoding="utf-8")
    scripts = re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", markup, re.S)
    assert len(scripts) == 1
    script = tmp_path / "studio.js"
    script.write_text(scripts[0], encoding="utf-8")
    subprocess.run(["node", "--check", str(script)], check=True, timeout=15)
    # No shared token or credential should be compiled into the public page.
    assert "STUDIO_ACCESS_TOKEN=" not in scripts[0]
    assert "localStorage.setItem('ownerToken'" not in scripts[0]
    assert "localStorage.setItem('aioclips-api-url'" in scripts[0]
