# Product roadmap

AIOClips AI is a private video studio progressing from a working local backend toward an easy, rights-aware mobile workflow. Statuses below reflect repository behavior, **not deployment readiness**.

## Release 0.3c — Music to Video mobile beta (November 2026)

- [x] Add fourth mobile-friendly Music to Video tab without replacing existing features
- [x] Authenticated MP3/WAV/M4A upload, configurable size and duration
- [x] Fail-closed mandatory commercial rights category, license/plan and HTTPS proof; private manifest
- [x] FFmpeg duration, tempo/BPM, beat times and energy analysis
- [x] Anthropic `claude-sonnet-5-5` theme JSON parsing with safe offline fallback
- [x] Optional Pexels/Pixabay stock searches and downloadable source credits; animated gradients without external keys
- [x] FFmpeg scene transitions, consistent color treatment, waveform, loudness normalization and 1080×1920 / 1920×1080 presets (internally upscaled)
- [x] Authenticated progress stages, mobile video preview, downloads and 24h best-effort retention
- [x] New automated rights, timing, JSON, stock query, credits and real FFmpeg render tests
- [ ] Real physical Android upload → render → preview/download acceptance on Render Free
- [ ] Validate longer-track memory usage, mobile connectivity and stock API integration with real keys
- [ ] Optional lyrics auto-transcription on a larger host, forced-aligned captions and stronger BPM detection
- [ ] Commercially verified music-generation provider (none enabled; no unverified promises)
- [ ] Durable private storage; Render Free may delete all files on idle/redeploy before 24h

**Status:** tested locally on GitHub-hosted Linux CI with FFmpeg, not independently confirmed from an Android device. [Full setup and constraints](MUSIC_TO_VIDEO.md).

## Release 0.3b — Authorized footage clipping beta (November 2026)

- [x] Build bearer-authenticated upload endpoint for owned or permitted third-party video files
- [x] Require declared reuse rights, evidence reference and explicit consent
- [x] Use existing FFmpeg audio-energy / scene-cut heuristics to suggest moments
- [x] Allow manual timeline trimming, original headline and captions
- [x] Queue 540×960 FFmpeg exports and reuse authenticated status/download endpoints
- [x] Enforce 40 MiB upload, 180-second video, 60-second clip, rate and job limits
- [x] Add scheduled expiry of private uploaded video and rendered MP4 files
- [x] Build responsive Android upload/analysis/clip UI and passing synthetic-media integration tests
- [ ] Physical Android test against deployed Render server (upload → suggestions → edited MP4 → download)
- [ ] Better semantic scene understanding and transcription-based highlighting
- [ ] Authorized import connectors where a service provides permitted source access (not unrestricted YouTube ripping)

**Current limit:** third-party YouTube links still act as references, not downloadable media feeds. The hosted beta clips user-uploaded files after a rights declaration. See [authorized-footage guide](AUTHORIZED_FOOTAGE_WORKFLOW.md).

## Release 0.3a — Hosted original-story mobile beta (November 2026)

- [x] Select Render Free for focused Docker-based rendering
- [x] Provision Render HTTPS service and store owner token in Render environment
- [x] Deploy CORS-limited original-story API with request limits and automatic temporary file expiry
- [x] Build GitHub Pages mobile UI with original story title, 1–8 beats, duration and consent declarations
- [x] Show live job status, secure MP4 preview and authenticated download in code
- [x] Separate reference-only URL mode from unavailable owned-footage upload
- [x] Add actual FFmpeg 540×960 API integration test and mobile UI syntax/contract tests
- [x] Confirm backend CI green and Render deployment reported live
- [ ] **Acceptance test on physical Android phone:** submit a story → receive ready status → preview/download real MP4
- [ ] Observe memory/CPU usage and longer-beat jobs on Render Free; correct any deployment-specific failures

**Current limitation:** an automated backend test and a Render 'live' deployment do not prove end-to-end Android rendering. Free-tier restarts discard temporary work. See [Android studio guide](MOBILE_STUDIO_DEPLOYMENT.md).

## Release 0.2 — Working local studio

- [x] Authenticated upload endpoint and playable-video validation
- [x] High-energy / scene-transition candidate generation
- [x] User-selectable in/out timestamps
- [x] Vertical MP4 rendering and private download
- [x] Animated karaoke-style ASS captions (estimated timing)
- [x] Optional server-side speech synthesis
- [x] Original graphical Short from independently written story beats
- [x] Synthetic FFmpeg smoke tests in GitHub Actions
- [ ] Hosted deployment with confirmed endpoint and real-phone smoke test

**Exit criteria:** private browser UI reaches a live API, uploads authorized media, renders and downloads MP4 on an Android device; service survives restart without losing production data.

## Release 0.3 — Production-grade foundation

- [ ] Persistent job queue, retries, timeouts and cancellation
- [ ] Structured logs, request IDs, health and readiness checks
- [ ] Harden media ingestion and bound storage/CPU consumption
- [ ] User accounts, secure sessions, expiring download links
- [ ] Review queue and provable source-rights metadata
- [ ] Automated media retention and deletion rules
- [ ] End-to-end frontend upload/render tests

**Exit criteria:** concurrent jobs and server restart tested; malicious file/input and unauthorized export access covered.

## Release 0.4 — Better storytelling

- [ ] Scene/audio/vision multimodal candidate ranking
- [ ] Explicit semantic moment labels with human verification
- [ ] Transcript generation and word-level forced-aligned caption timing
- [ ] Genre-specific visual layouts, fonts and safe-area presets
- [ ] Independently written draft suggestions based on user-provided verified facts
- [ ] Brand kit and consistent text/thumbnail system

**Exit criteria:** measured results on a licensed benchmark; editor can fix every selection and caption before export.

## Release 1.0 — Creator workflow

- [ ] Persistent projects, revisions, previews and approval history
- [ ] Rights and original-content policy enforcement in the UI
- [ ] Supported platform OAuth publishing with explicit approval
- [ ] Analytics imported from authorized channel accounts
- [ ] Mobile performance, accessibility and security review
- [ ] Versioned API and release notes

**Exit criteria:** a genuinely usable end-to-end workflow with published user instructions and verified deployment.

## Scope and non-goals

- **No DRM circumvention or unauthorized source downloads.**
- **No guarantee** of zero copyright claims, strikes or platform monetization restrictions.
- No watermark/cropping tricks to create a false claim of ownership.
- A YouTube reference link is not an authorized video feed.
- A generated graphical summary is not automatically verified for factual accuracy, originality or suitability for monetization.
