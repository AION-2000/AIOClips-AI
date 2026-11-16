"""Add-on Music to Video routes; existing AIOClips endpoints remain unchanged."""
from __future__ import annotations

import os
import re
import secrets
import shutil
import threading
import time
from concurrent.futures import Future
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from .audio_analyzer import UnsupportedAudio, analyze_audio, duration_and_codec
from .job_manifest import read_manifest, validate_rights, write_credits, write_manifest
from .music_provider import available_providers
from .renderer import PRESETS, RenderFailure, render_music
from .theme_planner import plan_theme
from .visual_fetcher import fetch_visuals

MUSIC_ROOT = Path(os.getenv("STORY_DATA_DIR", "/tmp/aioclips-stories")) / "music"
MUSIC_TTL_SECONDS = 24 * 3600
MAX_INPUT_MB = max(1, min(30, int(os.getenv("MUSIC_MAX_MB", "12"))))
MAX_INPUT_SECONDS = max(5, min(180, int(os.getenv("MUSIC_MAX_SECONDS", "90"))))
ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a"}
ALLOWED_MIMES = {
    "audio/mpeg", "audio/mp3", "audio/wav", "audio/x-wav",
    "audio/mp4", "audio/x-m4a", "audio/m4a", "application/octet-stream",
}
ID = re.compile(r"^[0-9a-f]{32}$")
LOCK = threading.RLock()
MUSIC_JOBS: dict[str, Future] = {}


def cleanup_music_jobs() -> None:
    MUSIC_ROOT.mkdir(parents=True, exist_ok=True)
    now = time.time()
    with LOCK:
        for folder in MUSIC_ROOT.iterdir():
            if not folder.is_dir() or not ID.fullmatch(folder.name):
                continue
            future = MUSIC_JOBS.get(folder.name)
            if (now - folder.stat().st_mtime >= MUSIC_TTL_SECONDS
                    and (future is None or future.done())):
                shutil.rmtree(folder, ignore_errors=True)
                MUSIC_JOBS.pop(folder.name, None)


def _janitor() -> None:
    while True:
        try:
            cleanup_music_jobs()
        except OSError:
            pass
        time.sleep(180)


def _job_folder(job_id: str) -> Path:
    if not ID.fullmatch(job_id):
        raise HTTPException(404, detail="Music job not found")
    folder = MUSIC_ROOT / job_id
    if not folder.is_dir():
        raise HTTPException(404, detail="Music job missing or expired")
    try:
        if time.time() - folder.stat().st_mtime >= MUSIC_TTL_SECONDS:
            future = MUSIC_JOBS.get(job_id)
            if future is None or future.done():
                shutil.rmtree(folder, ignore_errors=True)
                MUSIC_JOBS.pop(job_id, None)
                raise HTTPException(404, detail="Music job expired")
    except FileNotFoundError:
        raise HTTPException(404, detail="Music job missing")
    return folder


def _update(folder: Path, status: str, **fields) -> None:
    with LOCK:
        record = read_manifest(folder)
        record.update(fields)
        record["status"] = status
        write_manifest(folder, record)


def process_music_job(
    folder: Path, audio: Path, preset: str, style_note: str, lyrics: str,
    visualizer: bool, prefer_ai: bool, prefer_stock: bool,
) -> None:
    warnings: list[str] = []
    try:
        _update(folder, "analyzing")
        stats = analyze_audio(audio, MAX_INPUT_SECONDS)
        _update(folder, "theming", stats=stats.as_dict())
        theme, warning = plan_theme(stats, style_note, lyrics, prefer_ai)
        if warning:
            warnings.append(warning)
        _update(folder, "fetching_visuals", theme=theme, warnings=warnings)
        sources, credits, stock_warnings = (
            fetch_visuals(theme, folder, "portrait" if preset == "shorts" else "landscape")
            if prefer_stock else ({}, [], ["Stock discovery disabled; local visualizer used."])
        )
        warnings += stock_warnings
        write_credits(folder, credits)
        _update(folder, "rendering", credits_count=len(credits), warnings=warnings)
        output = folder / "video.mp4"
        render_music(audio, output, theme, sources, preset, visualizer, lyrics)
        _update(folder, "ready", download_url=f"/v1/music/jobs/{folder.name}/download",
                credits_url=f"/v1/music/jobs/{folder.name}/credits",
                title=theme["title"], description=theme["description"],
                hashtags=theme.get("hashtags", []), warnings=warnings)
    except (UnsupportedAudio, RenderFailure, ValueError) as exc:
        _update(folder, "error", detail=str(exc), warnings=warnings)
    except Exception:
        # Never log provider payloads, secrets or private rights proof.
        _update(folder, "error", detail="Music rendering failed; check hosting resources.",
                warnings=warnings)


def mount_music(app, authenticate: Callable, limit: Callable, executor,
                other_jobs: dict) -> None:
    router = APIRouter(prefix="/v1/music", dependencies=[Depends(authenticate)])

    @router.get("/config")
    def config():
        return {
            "max_audio_mb": MAX_INPUT_MB,
            "max_audio_seconds": MAX_INPUT_SECONDS,
            "presets": ["shorts", "youtube"],
            "music_generation_providers": available_providers(),
            "retention_hours": 24,
            "message": "AI music generation is disabled until a verified commercially licensed provider is configured.",
        }

    @router.post("/generate", status_code=501)
    def unavailable_generator():
        raise HTTPException(
            501, detail="No verified free commercial-use AI music generation provider is enabled. Upload licensed audio."
        )

    @router.post("/jobs", status_code=202)
    async def create_music_job(
        request: Request,
        audio: UploadFile = File(...),
        rights: str = Form(...),
        license_name: str = Form(..., max_length=160),
        proof_link: str = Form(..., max_length=500),
        rights_confirmed: bool = Form(...),
        style_note: str = Form(default="", max_length=300),
        lyrics: str = Form(default="", max_length=1500),
        preset: str = Form(default="shorts"),
        visualizer: bool = Form(default=True),
        prefer_ai: bool = Form(default=True),
        prefer_stock: bool = Form(default=True),
    ):
        limit(request, "music-create", 3, 600)
        if not rights_confirmed:
            raise HTTPException(403, detail="You must confirm commercial-use rights.")
        try:
            license_details = validate_rights(rights, license_name, proof_link)
        except ValueError as exc:
            raise HTTPException(422, detail=str(exc)) from exc
        if preset not in PRESETS:
            raise HTTPException(422, detail="Unsupported video preset.")
        suffix = Path(audio.filename or "").suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS or audio.content_type not in ALLOWED_MIMES:
            raise HTTPException(415, detail="Unsupported audio. Upload MP3, WAV or M4A.")
        # Refuse large requests before materializing file contents.
        length = request.headers.get("content-length")
        if length and (not length.isdecimal() or int(length) > MAX_INPUT_MB*1024*1024+16384):
            raise HTTPException(413, detail=f"Upload exceeds {MAX_INPUT_MB} MiB limit.")
        with LOCK:
            cleanup_music_jobs()
            pending = sum(not f.done() for f in MUSIC_JOBS.values())
            pending += sum(not j.future.done() for j in other_jobs.values())
            if pending >= 2:
                raise HTTPException(429, detail="Render queue busy. Try again soon.")
            if len(list(MUSIC_ROOT.iterdir())) >= 5:
                raise HTTPException(429, detail="Temporary music storage is full.")
        job_id = secrets.token_hex(16)
        folder = MUSIC_ROOT / job_id
        folder.mkdir(parents=True, exist_ok=False)
        source = folder / ("source" + suffix)
        bytes_read = 0
        try:
            with source.open("wb") as out:
                while chunk := await audio.read(256*1024):
                    bytes_read += len(chunk)
                    if bytes_read > MAX_INPUT_MB*1024*1024:
                        raise HTTPException(413, detail=f"Audio exceeds {MAX_INPUT_MB} MiB.")
                    out.write(chunk)
            if bytes_read < 64:
                raise HTTPException(415, detail="Audio is empty or unreadable.")
            try:
                duration = await run_in_threadpool(duration_and_codec, source)
            except UnsupportedAudio as exc:
                raise HTTPException(415, detail=str(exc)) from exc
            if duration > MAX_INPUT_SECONDS:
                raise HTTPException(
                    413, detail=f"Track exceeds {MAX_INPUT_SECONDS}-second limit."
                )
            write_manifest(folder, {
                "job_id": job_id, "status": "queued", "created_at": time.time(),
                "source_type": "uploaded_audio", "source_filename": (audio.filename or "")[:150],
                "rights": license_details, "duration_seconds": round(duration, 3),
                "preset": preset, "visualizer": visualizer,
                "style_note": style_note, "lyrics_supplied": bool(lyrics.strip()),
                "retention_hours": 24,
            })
            future = executor.submit(
                process_music_job, folder, source, preset, style_note, lyrics,
                visualizer, prefer_ai, prefer_stock,
            )
            with LOCK:
                MUSIC_JOBS[job_id] = future
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        finally:
            await audio.close()
        return {"job_id": job_id, "status": "queued",
                "status_url": f"/v1/music/jobs/{job_id}"}

    @router.get("/jobs/{job_id}")
    def music_status(job_id: str):
        folder = _job_folder(job_id)
        record = read_manifest(folder)
        # Only non-sensitive output metadata; license proof stays in manifest.
        response = {"job_id": job_id, "status": record["status"],
                    "warnings": record.get("warnings", []),
                    "stats": record.get("stats"),
                    "theme": record.get("theme")}
        for key in ("title", "description", "hashtags", "download_url",
                    "credits_url", "detail", "credits_count"):
            if key in record:
                response[key] = record[key]
        return response

    @router.get("/jobs/{job_id}/download")
    def download_music(job_id: str):
        folder = _job_folder(job_id)
        if read_manifest(folder)["status"] != "ready":
            raise HTTPException(409, detail="Music video is not ready.")
        target = folder / "video.mp4"
        if not target.is_file():
            raise HTTPException(404, detail="Rendered MP4 is no longer available.")
        return FileResponse(target, filename=f"AIOClips-Music-{job_id[:8]}.mp4",
                            media_type="video/mp4",
                            headers={"Cache-Control": "no-store"})

    @router.get("/jobs/{job_id}/manifest")
    def music_manifest(job_id: str):
        return read_manifest(_job_folder(job_id))

    @router.get("/jobs/{job_id}/credits")
    def music_credits(job_id: str):
        folder = _job_folder(job_id)
        if read_manifest(folder)["status"] not in ("ready", "rendering"):
            raise HTTPException(409, detail="Credits are not ready.")
        path = folder / "credits.txt"
        if not path.is_file():
            raise HTTPException(404, detail="Credits file missing.")
        return FileResponse(path, filename=f"AIOClips-Credits-{job_id[:8]}.txt",
                            media_type="text/plain",
                            headers={"Cache-Control": "no-store"})

    app.include_router(router)
    threading.Thread(target=_janitor, daemon=True, name="music-janitor").start()
