"""Parse supported match links without downloading third-party footage."""
from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be", "www.youtu.be"}


def parse_youtube_video_id(url: str) -> str:
    """Extract a canonical YouTube ID; reject untrusted hosts and malformed links."""
    if not isinstance(url, str) or len(url) > 2048:
        raise ValueError("Invalid URL")
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ValueError("Only HTTPS YouTube links are supported")
    if parsed.hostname not in _HOSTS or parsed.port not in (None, 443):
        raise ValueError("Unsupported video host")
    path = parsed.path.strip("/")
    if parsed.hostname in {"youtu.be", "www.youtu.be"}:
        candidate = path
    elif path == "watch":
        ids = parse_qs(parsed.query).get("v", [])
        candidate = ids[0] if len(ids) == 1 else ""
    elif path.startswith("shorts/") or path.startswith("live/") or path.startswith("embed/"):
        candidate = path.split("/", 1)[1]
    else:
        candidate = ""
    if not _VIDEO_ID.fullmatch(candidate):
        raise ValueError("Invalid YouTube video ID")
    return candidate


def canonical_youtube_url(url: str) -> str:
    return "https://www.youtube.com/watch?v=" + parse_youtube_video_id(url)
