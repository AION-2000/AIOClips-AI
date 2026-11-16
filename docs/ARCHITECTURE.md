# System architecture

> **Status: development alpha.** This document describes the implemented code paths and explicitly identifies work still required for a multi-user production deployment.

## Boundaries

AIOClips has three distinct surfaces:

1. **Static GitHub Pages preview** (`index.html`) — a UX concept only. No API calls, FFmpeg processing, user sessions or cloud exports.
2. **Private FastAPI studio** (`backend/app/server.py`, `studio.html`, `studio.js`) — the actual browser editor and API. Intended to run on a private Docker host.
3. **FFmpeg processing library** — Python functions for video-analysis heuristics, animated captions, optional speech synthesis, and MP4 exports.

## Media flow

```mermaid
flowchart TB
    Browser["Private browser studio"] -->|"Bearer token"| API["FastAPI API"]
    API -->|"File upload"| LocalMedia[("Private local media")]
    LocalMedia --> Analyze["Audio energy / scene-cut analysis"]
    Analyze --> Browser
    API --> Review{"Input rights or originality checks"}
    Review -->|"Authorized footage"| Clip["Clip Studio renderer"]
    Review -->|"Original written story"| Graphics["Original Story renderer"]
    Clip --> Voice["Optional server-side AI speech"]
    Graphics --> Voice
    Voice --> Caption["ASS caption builder"]
    Caption --> FFmpeg["FFmpeg render"]
    FFmpeg --> Exports[("Private MP4 exports")]
    Exports -->|"Authenticated download"| Browser
```

### Footage-based flow

- `POST /v1/uploads` accepts a multipart video file, writes it to a local `uploads` directory and probes its duration. Limit: **700 MiB** and **four hours**.
- `POST /v1/moments` ranks suggested windows by audio RMS energy. If there is no audio track, it falls back to a scene-transition heuristic.
- A suggestion is **not** a detected goal, semantic understanding of events, or verification of video claims.
- `POST /v1/renders` checks the source rights declaration, user-selected timestamp range and original caption fields, then submits an FFmpeg job.
- A successful render exposes `GET /v1/exports/{job_id}` to authenticated clients.

### Original Story flow

- `POST /v1/original-stories` accepts a title, **1–8 independently written beats**, optional narration script, and confirmations that underlying facts and originality have been reviewed.
- An optional YouTube reference URL is syntax-validated and **never downloaded, summarized, or used as a video source**.
- `original_story.py` creates new, abstract geometric video frames with a headline and story beats.
- Captions are estimated from script length. If configured, server-side AI narration creates a distinct audio track.
- This does not automatically verify copyright or legally certify the output.

## Component map

| Component | Responsibility | Current limitation |
| --- | --- | --- |
| `server.py` | Authenticated REST endpoints, upload, job tracking | Shared token, in-memory job table |
| `match_links.py` | Canonicalize YouTube IDs | Does not fetch video information |
| `url_safety.py` | Allowlisted URL preflight | No SSRF-safe fetcher implemented |
| `highlights.py` | Scene-cut suggestions | Not semantically aware |
| `match_clips.py` | Energy ranking, vertical FFmpeg video | Not a goal detector |
| `clip_studio.py` | Authorized media workflow | Rights declaration cannot independently prove licensing |
| `original_story.py` | Original graphic-story rendering | Not image/video generative AI |
| `voice.py` | Optional external speech synthesis | Needs key, credits, service availability |
| `captions.py` | Animated ASS text tracks | Pacing estimated, not forced-aligned |
| `approval.py` | Pure review-state policy | Not yet persisted/connected to upload UI |

## Security decisions

- Private endpoints use a server-side `STUDIO_ACCESS_TOKEN` and constant-time comparison.
- Python executes external FFmpeg binaries using argument arrays, not shell interpolation.
- Video writes and downloads use generated identifiers rather than user-provided paths.
- Docker image runs FFmpeg as a non-root user.
- Third-party reference URLs are treated as metadata, not permission to download media.
- Uploaded files are stored locally; production deployment still needs malware/media sandboxing, rate limits, storage cleanup, audit logs and robust resource quotas.

## Operational gaps before public launch

1. Durable queue (such as a worker backed by an appropriate datastore) replacing `ThreadPoolExecutor` and in-process `JOBS`.
2. Object storage with per-owner access policy, media retention and secure deletion.
3. User authentication and session lifecycle; revoke the single shared token.
4. Container CPU/memory limits, upload quotas, antivirus/content inspection, metrics and alerts.
5. Precise speech/caption alignment and failure recovery.
6. Explicit rights and factual review workflows, with immutable evidence and provenance.
7. End-to-end browser tests against a deployed service.
8. A separate authorized social-platform publishing integration, if later required.

Do not represent a green CI badge as verification of any of the above.
