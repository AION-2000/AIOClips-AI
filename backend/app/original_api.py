"""Single-owner HTTPS API for original graphical Shorts.

Temporary in-memory job metadata + temporary filesystem outputs. Jobs and videos
are removed after STORY_TTL_SECONDS. No user content is sent to GitHub Actions.
Keep STUDIO_ACCESS_TOKEN solely in the server environment, not static JS.
"""
from __future__ import annotations

import hmac
import os
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Request, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator
from starlette.concurrency import run_in_threadpool
from .clip_studio import FootageDeclaration, FootageRights, make_review_clip, suggest_video_moments
from .match_clips import duration_seconds

from .original_story import render_original_story

ORIGIN = "https://aion-2000.github.io"
DATA_DIR = Path(os.environ.get("STORY_DATA_DIR", "/tmp/aioclips-stories")).resolve()
TTL_SECONDS = max(300, min(7200, int(os.environ.get("STORY_TTL_SECONDS", "1800"))))
ID_PATTERN = re.compile(r"^[a-f0-9]{32}$")
MAX_FOOTAGE_BYTES = 40 * 1024 * 1024
MAX_FOOTAGE_SECONDS = 180
EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="original-short")
LOCK = threading.RLock()
REQUESTS: dict[str, deque[float]] = defaultdict(deque)


@dataclass
class Job:
    future: Future
    output: Path
    created_at: float
    source: Path | None = None


@dataclass
class FootageAsset:
    path: Path
    duration: float
    rights: FootageRights
    evidence: str
    created_at: float


JOBS: dict[str, Job] = {}
UPLOADED: dict[str, FootageAsset] = {}
app = FastAPI(
    title="AIOClips private original story renderer",
    version="0.3.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[ORIGIN],
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=False,
    max_age=600,
)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    if request.url.path == "/v1/footage/uploads":
        content_length = request.headers.get("content-length")
        if content_length is not None and (
            not content_length.isdecimal()
            or int(content_length) > MAX_FOOTAGE_BYTES + 65536
        ):
            return JSONResponse(status_code=413, content={"detail": "Footage exceeds the 40 MB limit"})
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-Frame-Options"] = "DENY"
    return response


def _limit(request: Request, scope: str, maximum: int, interval: int) -> None:
    # Use the ASGI peer, not an attacker-controlled X-Forwarded-For header.
    peer = request.client.host if request.client else "unknown"
    now = time.monotonic()
    key = f"{scope}:{peer}"
    with LOCK:
        bucket = REQUESTS[key]
        while bucket and bucket[0] <= now - interval:
            bucket.popleft()
        if len(bucket) >= maximum:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Try again later.",
                headers={"Retry-After": str(interval)},
            )
        bucket.append(now)
        # Bound the number of remembered peers on a public endpoint.
        if len(REQUESTS) > 1024:
            for old_key in list(REQUESTS)[:256]:
                if old_key != key:
                    del REQUESTS[old_key]


def require_owner(request: Request, authorization: str | None = Header(default=None)) -> None:
    _limit(request, "auth", maximum=30, interval=60)
    expected = os.environ.get("STUDIO_ACCESS_TOKEN", "")
    if len(expected) < 32:
        raise HTTPException(status_code=503, detail="Server owner token is not configured")
    supplied = authorization or ""
    # Compare fixed-length hashes, avoiding token-length timing differences.
    import hashlib
    good = hmac.compare_digest(
        hashlib.sha256(supplied.encode()).digest(),
        hashlib.sha256(("Bearer " + expected).encode()).digest(),
    )
    if not good:
        raise HTTPException(
            status_code=401,
            detail="Invalid owner passphrase",
            headers={"WWW-Authenticate": "Bearer"},
        )


class StoryInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=110)
    beats: list[str] = Field(min_length=1, max_length=8)
    seconds_per_beat: int = Field(default=5, ge=3, le=10)
    facts_verified: bool
    independently_written: bool

    @field_validator("title")
    @classmethod
    def title_sane(cls, text: str) -> str:
        return cls.clean_text(text, 110)

    @field_validator("beats")
    @classmethod
    def beats_sane(cls, items: list[str]) -> list[str]:
        return [cls.clean_text(text, 180) for text in items]

    @staticmethod
    def clean_text(value: str, maximum: int) -> str:
        if not isinstance(value, str):
            raise ValueError("Text required")
        if re.search(r"[\x00-\x1f\x7f]", value):
            raise ValueError("Control characters are not allowed")
        cleaned = " ".join(value.split())
        if not cleaned or len(cleaned) > maximum:
            raise ValueError("Text must be nonempty and within the character limit")
        return cleaned


def cleanup_expired() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    now = time.time()
    with LOCK:
        for job_id, job in list(JOBS.items()):
            if job.future.done() and now - job.created_at > TTL_SECONDS:
                job.output.unlink(missing_ok=True)
                del JOBS[job_id]
        # Also prune orphan videos left by a container/process restart.
        for output in DATA_DIR.glob("*.mp4"):
            if (now - output.stat().st_mtime > TTL_SECONDS
                    and not any(x.output == output and not x.future.done()
                                for x in JOBS.values())):
                output.unlink(missing_ok=True)
        uploads_dir = DATA_DIR / "uploads"
        for asset_id, asset in list(UPLOADED.items()):
            using_source = any(
                job.source == asset.path and not job.future.done()
                for job in JOBS.values()
            )
            if now - asset.created_at > TTL_SECONDS and not using_source:
                asset.path.unlink(missing_ok=True)
                del UPLOADED[asset_id]
        if uploads_dir.is_dir():
            for file in uploads_dir.glob("*.media"):
                if (now - file.stat().st_mtime > TTL_SECONDS
                    and not any(job.source == file and not job.future.done()
                                for job in JOBS.values())):
                    file.unlink(missing_ok=True)


def _janitor() -> None:
    while True:
        try:
            cleanup_expired()
        except OSError:
            pass
        time.sleep(60)


threading.Thread(target=_janitor, name="story-janitor", daemon=True).start()


def _render(job_output: Path, title: str, beats: list[str], duration: int) -> None:
    try:
        render_original_story(
            title=title,
            beats=beats,
            output=job_output,
            seconds_per_beat=duration,
            size=(540, 960),
        )
    except Exception:
        job_output.unlink(missing_ok=True)
        raise


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "aioclips-original-story", "configured":
            len(os.environ.get("STUDIO_ACCESS_TOKEN", "")) >= 32}


@app.post("/v1/story/jobs", status_code=202, dependencies=[Depends(require_owner)])
def create_story(body: StoryInput, request: Request):
    _limit(request, "create", maximum=5, interval=600)
    if not body.facts_verified or not body.independently_written:
        raise HTTPException(
            status_code=403,
            detail="Confirm the facts are checked and the story is independently written.",
        )
    with LOCK:
        cleanup_expired()
        if sum(not job.future.done() for job in JOBS.values()) >= 2:
            raise HTTPException(status_code=429, detail="Render queue is full. Try later.")
        job_id = secrets.token_hex(16)
        output = DATA_DIR / f"{job_id}.mp4"
        future = EXECUTOR.submit(
            _render, output, body.title, body.beats, body.seconds_per_beat
        )
        JOBS[job_id] = Job(future=future, output=output, created_at=time.time())
    return {"job_id": job_id, "status": "queued",
            "resolution": "540x960", "seconds": len(body.beats) * body.seconds_per_beat}


def _get_job(job_id: str) -> Job:
    if not ID_PATTERN.fullmatch(job_id):
        raise HTTPException(status_code=404, detail="Job not found")
    with LOCK:
        job = JOBS.get(job_id)
        if job and job.future.done() and time.time() - job.created_at > TTL_SECONDS:
            job.output.unlink(missing_ok=True)
            del JOBS[job_id]
            job = None
    if not job:
        raise HTTPException(status_code=404, detail="Job missing or expired")
    return job


@app.get("/v1/story/jobs/{job_id}", dependencies=[Depends(require_owner)])
def story_status(job_id: str):
    job = _get_job(job_id)
    if not job.future.done():
        return {"status": "processing"}
    if job.future.exception() is not None or not job.output.is_file():
        return {"status": "error", "detail": "Rendering failed. Please try again."}
    return {"status": "ready", "download_url": f"/v1/story/jobs/{job_id}/download"}


@app.get("/v1/story/jobs/{job_id}/download", dependencies=[Depends(require_owner)])
def download_story(job_id: str):
    job = _get_job(job_id)
    if not job.future.done() or job.future.exception() is not None or not job.output.is_file():
        raise HTTPException(status_code=409, detail="Video is not ready")
    return FileResponse(
        job.output, filename=f"AIOClips-{job_id[:8]}.mp4",
        media_type="video/mp4", headers={"Cache-Control": "no-store"},
    )


# Hosted footage workflow — uploaded media with explicit edit/reuse permission.
# External video URLs are never fetched, downloaded or used as an import source.


def _media(asset_id: str) -> FootageAsset:
    if not ID_PATTERN.fullmatch(asset_id):
        raise HTTPException(status_code=404, detail="Video not found")
    with LOCK:
        asset = UPLOADED.get(asset_id)
        if asset and time.time() - asset.created_at > TTL_SECONDS:
            in_use = any(
                job.source == asset.path and not job.future.done()
                for job in JOBS.values()
            )
            if not in_use:
                asset.path.unlink(missing_ok=True)
                del UPLOADED[asset_id]
                asset = None
    if not asset or not asset.path.is_file():
        raise HTTPException(status_code=404, detail="Video missing or expired")
    return asset


@app.post("/v1/footage/uploads", status_code=201, dependencies=[Depends(require_owner)])
async def upload_footage(
    request: Request,
    video: UploadFile = File(...),
    rights: FootageRights = Form(...),
    rights_evidence: str = Form(..., min_length=8, max_length=600),
    permission_to_edit: bool = Form(...),
):
    _limit(request, "uploads", maximum=3, interval=600)
    if not permission_to_edit:
        raise HTTPException(status_code=403, detail="Confirm permission to edit this footage.")
    if not rights_evidence.strip():
        raise HTTPException(status_code=422, detail="Source or rights evidence required.")
    if video.content_type not in {
        "video/mp4", "video/quicktime", "video/webm",
        "video/x-matroska", "application/octet-stream",
    }:
        raise HTTPException(status_code=415, detail="Unsupported video content type.")
    with LOCK:
        cleanup_expired()
        if len(UPLOADED) >= 3:
            raise HTTPException(status_code=429, detail="Maximum 3 stored videos. Try later.")
    upload_dir = DATA_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    asset_id = secrets.token_hex(16)
    target = upload_dir / (asset_id + ".media")
    partial = upload_dir / (asset_id + ".part")
    total = 0
    try:
        with partial.open("wb") as handle:
            while chunk := await video.read(512 * 1024):
                total += len(chunk)
                if total > MAX_FOOTAGE_BYTES:
                    raise HTTPException(status_code=413, detail="Video exceeds the 40 MB limit.")
                handle.write(chunk)
        if not total:
            raise HTTPException(status_code=422, detail="Video cannot be empty.")
        try:
            duration = await run_in_threadpool(duration_seconds, partial)
        except Exception as exc:
            raise HTTPException(status_code=415, detail="Unreadable video footage.") from exc
        if duration > MAX_FOOTAGE_SECONDS:
            raise HTTPException(status_code=413, detail="Video duration exceeds 3 minutes.")
        partial.replace(target)
        with LOCK:
            UPLOADED[asset_id] = FootageAsset(
                path=target, duration=duration, rights=rights,
                evidence=rights_evidence.strip(), created_at=time.time(),
            )
        return {"asset_id": asset_id, "duration": round(duration, 2),
                "expires_in_seconds": TTL_SECONDS}
    except Exception:
        partial.unlink(missing_ok=True)
        target.unlink(missing_ok=True)
        raise
    finally:
        await video.close()


class HighlightsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    seconds: float = Field(default=15, ge=1, le=60, allow_inf_nan=False)
    limit: int = Field(default=5, ge=1, le=6)


@app.post("/v1/footage/{asset_id}/highlights", dependencies=[Depends(require_owner)])
async def highlight_footage(asset_id: str, body: HighlightsInput, request: Request):
    _limit(request, "analysis", maximum=6, interval=600)
    asset = _media(asset_id)
    try:
        moments = await run_in_threadpool(
            suggest_video_moments, asset.path,
            clip_seconds=min(body.seconds, asset.duration), limit=body.limit,
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to analyze this video.") from exc
    # Scores represent audio energy or scene changes, not semantic event recognition.
    return {"asset_id": asset_id, "duration": round(asset.duration, 2),
            "moments": [
                {"start": m.start, "end": m.end, "score": m.score, "kind": m.kind}
                for m in moments
            ],
            "note": "Heuristic energy/scene suggestions; review before using."}


class ClipInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    start: float = Field(ge=0, allow_inf_nan=False)
    end: float = Field(gt=0, allow_inf_nan=False)
    headline: str = Field(min_length=1, max_length=90, pattern=r"^[\w ,.!?\-]+$")
    caption_script: str = Field(min_length=1, max_length=600)
    permission_to_publish: bool

    @field_validator("caption_script")
    @classmethod
    def caption_sane(cls, value: str) -> str:
        return StoryInput.clean_text(value, 600)


def _render_footage(asset: FootageAsset, output: Path, body: ClipInput) -> None:
    try:
        make_review_clip(
            asset.path, output, start=body.start, end=body.end,
            rights=FootageDeclaration(
                rights=asset.rights, evidence=asset.evidence,
                permission_to_publish=body.permission_to_publish,
            ),
            headline=body.headline,
            caption_script=body.caption_script,
            size=(540, 960),
        )
    except Exception:
        output.unlink(missing_ok=True)
        raise
    finally:
        output.with_suffix(".ass").unlink(missing_ok=True)


@app.post("/v1/footage/{asset_id}/clips", status_code=202, dependencies=[Depends(require_owner)])
def create_footage_clip(asset_id: str, body: ClipInput, request: Request):
    _limit(request, "clips", maximum=5, interval=600)
    asset = _media(asset_id)
    if not body.permission_to_publish:
        raise HTTPException(status_code=403, detail="Confirm source reuse and publishing rights.")
    if body.end <= body.start or body.end > asset.duration + 0.0001 or body.end - body.start > 60:
        raise HTTPException(status_code=422, detail="Select a 1–60 second segment within the uploaded video.")
    if body.end - body.start < 1:
        raise HTTPException(status_code=422, detail="Clips must be at least 1 second.")
    with LOCK:
        cleanup_expired()
        if sum(not job.future.done() for job in JOBS.values()) >= 2:
            raise HTTPException(status_code=429, detail="Render queue is full.")
        job_id = secrets.token_hex(16)
        output = DATA_DIR / (job_id + ".mp4")
        future = EXECUTOR.submit(_render_footage, asset, output, body)
        JOBS[job_id] = Job(
            future=future, output=output, created_at=time.time(),
            source=asset.path,
        )
    return {"job_id": job_id, "status": "queued", "resolution": "540x960",
            "seconds": round(body.end - body.start, 2)}
