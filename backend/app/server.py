"""Single-owner AIOClips backend: authenticated uploads, clip suggestions and exports.

Run on a private FFmpeg-enabled server, not GitHub Pages. For production, put a
persistent worker queue and object storage behind the API (in-memory jobs are an MVP).
"""
from __future__ import annotations

import hmac
import os
import re
import secrets
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .clip_studio import FootageDeclaration, FootageRights, make_review_clip, suggest_video_moments
from .match_clips import duration_seconds
from .match_links import canonical_youtube_url
from .original_story import render_original_story

ROOT = Path(os.environ.get("STUDIO_DATA_DIR", "/tmp/aioclips-data")).resolve()
MAX_UPLOAD = 700 * 1024 * 1024
MAX_DURATION = 4 * 60 * 60
ASSET_ID = re.compile(r"^[0-9a-f]{32}$")
POOL = ThreadPoolExecutor(max_workers=1, thread_name_prefix="aioclips-render")
JOBS: dict[str, tuple[Future, Path]] = {}

app = FastAPI(
    title="AIOClips AI - Private Media Studio",
    description="Authorized footage only; this app does not bypass social platform download restrictions.",
    version="0.2.0",
)


def authenticated(authorization: str | None = Header(default=None)) -> None:
    token = os.environ.get("STUDIO_ACCESS_TOKEN")
    if not token:
        raise HTTPException(status_code=503, detail="Studio access token not configured")
    provided = authorization or ""
    if not hmac.compare_digest(provided, f"Bearer {token}"):
        raise HTTPException(
            status_code=401, detail="Invalid access token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _asset(asset_id: str) -> Path:
    if not ASSET_ID.fullmatch(asset_id):
        raise HTTPException(status_code=400, detail="Invalid asset ID")
    target = ROOT / "uploads" / f"{asset_id}.media"
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Media not found")
    return target


@app.get("/")
def studio_page():
    return FileResponse(Path(__file__).with_name("studio.html"), media_type="text/html")


@app.get("/studio.js")
def studio_script():
    return FileResponse(Path(__file__).with_name("studio.js"), media_type="text/javascript")


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "aioclips-studio"}


@app.post("/v1/links", dependencies=[Depends(authenticated)])
def inspect_youtube_link(body: dict):
    try:
        url = canonical_youtube_url(body.get("url", ""))
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail="Invalid YouTube video link") from exc
    return {
        "url": url,
        "importable": False,
        "message": "YouTube link recognized. Provide a separately authorized original media file for clipping.",
    }


@app.post("/v1/uploads", dependencies=[Depends(authenticated)])
async def upload_video(video: UploadFile = File(...)):
    ROOT.joinpath("uploads").mkdir(parents=True, exist_ok=True)
    asset_id = secrets.token_hex(16)
    target = ROOT / "uploads" / f"{asset_id}.media"
    total = 0
    try:
        with target.open("wb") as handle:
            while True:
                chunk = await video.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_UPLOAD:
                    raise HTTPException(status_code=413, detail="Video exceeds 700 MB limit")
                handle.write(chunk)
        if not total:
            raise HTTPException(status_code=400, detail="Empty video")
        try:
            duration = await run_in_threadpool(duration_seconds, target)
        except Exception as exc:
            raise HTTPException(status_code=415, detail="File is not a readable video") from exc
        if duration > MAX_DURATION:
            raise HTTPException(status_code=413, detail="Video longer than 4 hours")
        return {"asset_id": asset_id, "duration": duration, "filename": video.filename}
    except Exception:
        target.unlink(missing_ok=True)
        raise
    finally:
        await video.close()


class MomentRequest(BaseModel):
    asset_id: str
    seconds: float = Field(default=20, ge=1, le=180)
    limit: int = Field(default=5, ge=1, le=10)


@app.post("/v1/moments", dependencies=[Depends(authenticated)])
async def moments(body: MomentRequest):
    path = _asset(body.asset_id)
    try:
        candidates = await run_in_threadpool(
            suggest_video_moments, path, clip_seconds=body.seconds, limit=body.limit
        )
    except Exception as exc:
        raise HTTPException(status_code=422, detail="Unable to analyze video") from exc
    return {"asset_id": body.asset_id, "moments": [
        {"start": m.start, "end": m.end, "score": m.score, "kind": m.kind}
        for m in candidates
    ], "note": "These are automatic suggestions, not verified descriptions of events."}


class RenderRequest(BaseModel):
    asset_id: str
    start: float = Field(ge=0)
    end: float = Field(gt=0)
    headline: str = Field(min_length=1, max_length=90)
    caption_script: str = Field(min_length=1, max_length=3000)
    narration_script: str | None = Field(default=None, max_length=4000)
    rights: FootageRights
    rights_evidence: str = Field(min_length=1, max_length=1000)
    permission_to_publish: bool


@app.post("/v1/renders", dependencies=[Depends(authenticated)], status_code=202)
def render(body: RenderRequest):
    source = _asset(body.asset_id)
    if body.end <= body.start:
        raise HTTPException(status_code=422, detail="Invalid clip time range")
    duration = duration_seconds(source)
    if body.end > duration:
        raise HTTPException(status_code=422, detail="Clip exceeds video duration")
    declaration = FootageDeclaration(
        rights=body.rights,
        evidence=body.rights_evidence,
        permission_to_publish=body.permission_to_publish,
    )
    try:
        declaration.validate()
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    ROOT.joinpath("exports").mkdir(parents=True, exist_ok=True)
    job_id = secrets.token_hex(16)
    output = ROOT / "exports" / f"{job_id}.mp4"
    # No automatic publication is performed. Review and license checks remain
    # a separate, mandatory human decision.
    future = POOL.submit(
        make_review_clip, source, output, start=body.start, end=body.end,
        rights=declaration, headline=body.headline, caption_script=body.caption_script,
        narration_script=body.narration_script,
    )
    JOBS[job_id] = (future, output)
    return {"job_id": job_id, "status": "queued"}


class OriginalStoryRequest(BaseModel):
    reference_url: str | None = Field(default=None, max_length=2048)
    title: str = Field(min_length=1, max_length=110)
    beats: list[str] = Field(min_length=1, max_length=8)
    narration_script: str | None = Field(default=None, max_length=3000)
    seconds_per_beat: int = Field(default=5, ge=3, le=10)
    facts_verified: bool
    independently_written: bool


@app.post("/v1/original-stories", dependencies=[Depends(authenticated)], status_code=202)
def original_story(body: OriginalStoryRequest):
    """Create original motion graphics without reproducing third-party footage.

    The optional YouTube URL is a reference only and is never fetched.
    Original expression and fact verification remain human responsibilities.
    """
    if not body.facts_verified or not body.independently_written:
        raise HTTPException(
            status_code=403,
            detail="Verify the facts and confirm your story is independently written.",
        )
    if body.reference_url:
        try:
            canonical_youtube_url(body.reference_url)
        except (ValueError, TypeError) as exc:
            raise HTTPException(status_code=422, detail="Invalid YouTube reference") from exc
    if any(not beat.strip() or len(beat) > 180 for beat in body.beats):
        raise HTTPException(status_code=422, detail="Each story beat must be 1-180 characters")
    ROOT.joinpath("exports").mkdir(parents=True, exist_ok=True)
    job_id = secrets.token_hex(16)
    output = ROOT / "exports" / f"{job_id}.mp4"
    future = POOL.submit(
        render_original_story,
        title=body.title,
        beats=body.beats,
        output=output,
        narration_script=body.narration_script,
        seconds_per_beat=body.seconds_per_beat,
    )
    JOBS[job_id] = (future, output)
    return {
        "job_id": job_id, "status": "queued", "source": "original graphics only",
        "note": "No frames or audio are downloaded or copied from the reference.",
    }


@app.get("/v1/renders/{job_id}", dependencies=[Depends(authenticated)])
def render_status(job_id: str):
    if not ASSET_ID.fullmatch(job_id) or job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Render not found")
    future, _ = JOBS[job_id]
    if not future.done():
        return {"status": "processing"}
    if future.exception() is not None:
        return {"status": "error", "detail": "Video processing failed; check server logs"}
    return {"status": "ready", "download_url": f"/v1/exports/{job_id}"}


@app.get("/v1/exports/{job_id}", dependencies=[Depends(authenticated)])
def download_render(job_id: str):
    if not ASSET_ID.fullmatch(job_id) or job_id not in JOBS:
        raise HTTPException(status_code=404, detail="Export not found")
    future, path = JOBS[job_id]
    if not future.done() or future.exception() is not None or not path.is_file():
        raise HTTPException(status_code=409, detail="Export is not ready")
    return FileResponse(
        path, filename=f"AIOClips-{job_id[:8]}.mp4",
        media_type="video/mp4", headers={"Cache-Control": "no-store"}
    )
