"""Rights-aware stock-video discovery with guarded HTTPS downloads.

Pexels/Pixabay are optional; no keys means procedural FFmpeg visuals. Restrict
downloads to documented provider CDN hosts; no redirects or arbitrary URLs.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from urllib.parse import urlsplit

import httpx

PEXELS_LICENSE = "https://www.pexels.com/license/"
PIXABAY_LICENSE = "https://pixabay.com/service/license-summary/"
ALLOWED_CDNS = {"videos.pexels.com", "cdn.pixabay.com"}
MAX_STOCK_DOWNLOAD = 12 * 1024 * 1024


class StockRateLimit(Exception):
    pass


class StockUnavailable(Exception):
    pass


def search_query(keywords: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9 ]+", " ", keywords)
    return " ".join(text.split()[:6]).strip()[:80] or "abstract nature"


def search_candidates(keywords: str, orientation: str, client: httpx.Client) -> list[dict]:
    q = search_query(keywords)
    orientation = "landscape" if orientation == "landscape" else "portrait"
    candidates: list[dict] = []
    pexels = os.getenv("PEXELS_API_KEY", "").strip()
    if pexels:
        res = client.get(
            "https://api.pexels.com/v1/videos/search",
            params={"query": q, "per_page": 3, "orientation": orientation},
            headers={"Authorization": pexels},
        )
        if res.status_code == 429:
            raise StockRateLimit("Pexels API rate limit reached.")
        res.raise_for_status()
        for video in res.json().get("videos", [])[:3]:
            assets = sorted(video.get("video_files", []),
                            key=lambda x: (x.get("width") or 10000))
            for file in assets:
                link = file.get("link", "")
                width, height = file.get("width") or 0, file.get("height") or 0
                if width > 0 and height > 0 and (
                    (orientation == "portrait" and height > width)
                    or (orientation == "landscape" and width > height)
                ):
                    candidates.append({
                        "provider": "Pexels", "url": link,
                        "source_page": str(video.get("url", "")),
                        "creator": str(video.get("user", {}).get("name", "Unknown")),
                        "license_url": PEXELS_LICENSE,
                    })
                    break
    pixabay = os.getenv("PIXABAY_API_KEY", "").strip()
    if pixabay and not candidates:
        res = client.get(
            "https://pixabay.com/api/videos/",
            params={"key": pixabay, "q": q, "per_page": 3, "safesearch": "true"},
        )
        if res.status_code == 429:
            raise StockRateLimit("Pixabay API rate limit reached.")
        res.raise_for_status()
        for video in res.json().get("hits", [])[:3]:
            rendition = video.get("videos", {}).get("tiny", {})
            url = rendition.get("url", "")
            candidates.append({
                "provider": "Pixabay", "url": url,
                "source_page": str(video.get("pageURL", "")),
                "creator": str(video.get("user", "Unknown")),
                "license_url": PIXABAY_LICENSE,
            })
    return candidates


def download_stock(url: str, destination: Path, client: httpx.Client) -> None:
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname not in ALLOWED_CDNS
            or parts.username or parts.password or parts.port not in (None, 443)):
        raise StockUnavailable("Stock CDN URL was not on the allowlist.")
    total = 0
    try:
        with client.stream("GET", url, follow_redirects=False) as response:
            if response.status_code == 429:
                raise StockRateLimit("Stock download rate limit reached.")
            if response.status_code != 200:
                raise StockUnavailable("Stock video download unavailable.")
            header = response.headers.get("content-length", "")
            if header.isdecimal() and int(header) > MAX_STOCK_DOWNLOAD:
                raise StockUnavailable("Stock clip exceeds download size limit.")
            with destination.open("wb") as handle:
                for chunk in response.iter_bytes(chunk_size=64 * 1024):
                    total += len(chunk)
                    if total > MAX_STOCK_DOWNLOAD:
                        raise StockUnavailable("Stock clip exceeds download size limit.")
                    handle.write(chunk)
        if total < 256:
            raise StockUnavailable("Empty stock footage file.")
    except Exception:
        destination.unlink(missing_ok=True)
        raise


def fetch_visuals(theme: dict, destination: Path, orientation: str) -> tuple[dict, list[dict], list[str]]:
    """Return per-scene downloaded footage paths, credits, warning strings.

    Limit to two stock downloads on the small Free worker. Remaining scenes
    get local procedural visuals; no remote API calls without configured keys.
    """
    sources: dict[int, Path] = {}
    credits: list[dict] = []
    warnings: list[str] = []
    if not os.getenv("PEXELS_API_KEY") and not os.getenv("PIXABAY_API_KEY"):
        return sources, credits, ["Stock keys absent: rendered free FFmpeg visuals."]
    with httpx.Client(timeout=12, follow_redirects=False) as client:
        for i, scene in enumerate(theme["scenes"][:2]):
            try:
                candidates = search_candidates(scene["keywords"], orientation, client)
                if not candidates:
                    raise StockUnavailable("No matching stock footage found.")
                last_error = None
                for item in candidates[:2]:
                    path = destination / f"stock_{i}.mp4"
                    try:
                        download_stock(item["url"], path, client)
                    except (httpx.HTTPError, StockUnavailable, StockRateLimit) as exc:
                        last_error = exc
                        continue
                    sources[i] = path
                    credits.append({
                        "scene_index": i + 1, "provider": item["provider"],
                        "creator": item["creator"], "source_page": item["source_page"],
                        "license_url": item["license_url"],
                    })
                    break
                if i not in sources:
                    raise last_error or StockUnavailable("No usable footage found.")
            except StockRateLimit as exc:
                warnings.append(str(exc) + " Using locally generated visuals.")
                break
            except (StockUnavailable, httpx.HTTPError, ValueError, KeyError) as exc:
                warnings.append(f"Scene {i+1}: stock unavailable ({type(exc).__name__}); using generated visuals.")
    return sources, credits, warnings
