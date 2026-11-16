# Product roadmap

AIOClips AI is a private video studio progressing from a working local backend toward an easy, rights-aware mobile workflow. Statuses below reflect repository behavior, **not deployment readiness**.

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
