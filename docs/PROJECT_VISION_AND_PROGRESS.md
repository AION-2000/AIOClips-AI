# AIOClips AI — Project Vision, Progress & Delivery Plan

**Project status:** Development alpha / working prototype  
**Last reviewed:** 16 November 2026  
**Repository:** https://github.com/AION-2000/AIOClips-AI  
**Live frontend preview:** https://aion-2000.github.io/AIOClips-AI/

## 1. Our goal

Build **AIOClips AI**, a polished, Android-friendly, secure video-creation studio that lets a creator paste a supported video link or upload video they own or are licensed to edit, discover useful moments, turn selected segments into vertical Shorts, add readable captions and optional narration, preview results, and download finished MP4 files.

A second workflow will generate **original graphical Shorts** from independently written, verified story beats without importing third-party footage.

The target experience is: **Open website → paste link or upload authorized media → choose content/clip → generate → review → download**. The finished application should work from an Android browser without leaving a PC running.

### Important product distinction

A **pasted YouTube link** currently acts only as a validated reference. It is *not* a license or technical authorization to download, reuse, or clip the underlying video. Source-footage processing requires owned/licensed media or an appropriately authorized integration. We will not promise universal one-click extraction from arbitrary third-party links.

## 2. What has been implemented

| Area | Current state | Evidence / notes |
| --- | --- | --- |
| GitHub repository and documentation | Done | Public repository with README, architecture, roadmap, security and deployment guides |
| Public live website | Deployed | GitHub Pages static preview; last Pages workflow succeeded after the link-input change |
| Responsive preview UI | Implemented | `index.html` includes local draft/review interactions; no production API connection |
| Paste Video Link field | Implemented in static UI | Validates YouTube watch, Shorts, live, embed and youtu.be links in browser; **does not fetch or clip footage** |
| Private studio API | Implemented locally | FastAPI in `backend/app/server.py` with bearer-token access |
| Authorized media upload | Implemented locally | File validation and size/duration constraints; not available through Pages |
| Highlight suggestions | Heuristic implementation | Audio-energy and scene-cut suggestions, **not AI semantic goal/event detection** |
| Footage-to-Short rendering | Implemented locally | FFmpeg vertical MP4 and captions, subject to rights declaration |
| Original Story rendering | Implemented locally and in Actions | Generates original geometric video from title and story beats |
| Cloud batch renderer | **Verified** | GitHub Actions successfully rendered and uploaded an original-story MP4 |
| Automated backend tests | **Verified** | 76 tests passed in GitHub Actions on 16 Nov 2026 |
| Cloud-to-website integration | Not implemented | GitHub Pages cannot safely store GitHub API credentials |
| Full production deployment | Not implemented | Private FastAPI studio is not publicly hosted |

## 3. Technical architecture today

**A. GitHub Pages — public UI preview**
- `index.html`: responsive demo, local draft approval, and safe URL syntax validation.
- Published by `.github/workflows/pages.yml`.
- Static hosting only: **no private server, database, video analysis or FFmpeg**.

**B. FastAPI — functional private studio**
- `backend/app/server.py` provides authenticated uploads, moment suggestions, original-story requests, render jobs and downloads.
- `backend/app/studio.html` and `studio.js` are the actual private studio UI.
- `backend/app/match_clips.py`, `highlights.py`, `clip_studio.py`, `captions.py`, `voice.py`, `original_story.py` contain rendering and analysis logic.
- Currently relies on local storage and in-memory jobs. A secure persistent production service is still required.

**C. GitHub Actions — free-tier cloud rendering prototype**
- `.github/workflows/batch-original-story.yml`: manual original-story workflow and automatic non-sensitive smoke render on renderer changes.
- `backend/batch_render.py`: validates a short title and 1–8 story beats, renders 540×960 MP4.
- Finished video is uploaded as a short-retention workflow artifact.
- This is **not** a general-purpose upload API or an always-on video service.

### Current user journey

```text
GitHub Pages website
  ├─ Paste YouTube link → validate/reference only (works)
  └─ Draft/review concept → local browser demo (works)

Private FastAPI studio (local/separately hosted)
  └─ Upload authorized video → suggest moments → render → download (implemented locally)

GitHub Actions
  └─ Original story inputs → FFmpeg cloud render → MP4 artifact (verified)
```

These are **three separate surfaces**. They are not yet connected into a single production mobile app.

## 4. Verified milestones

1. Created and published the static GitHub Pages preview.
2. Implemented a rights-aware FastAPI studio and FFmpeg rendering logic.
3. Added the cloud batch renderer, validation tests and user guide.
4. **Backend tests passed: 76 passed, 1 warning.** Run: https://github.com/AION-2000/AIOClips-AI/actions/runs/43917431981
5. **First cloud render succeeded** and produced an MP4 artifact. Run: https://github.com/AION-2000/AIOClips-AI/actions/runs/43917971065
6. Added a **Live Preview** and **Cloud Renderer** link to the repository README.
7. Added the **Paste Video Link** form and local YouTube URL validation. Commit: https://github.com/AION-2000/AIOClips-AI/commit/65e1ba905fd2ecdf8b7e2deacf4c9c728e53b44e
8. Confirmed the GitHub Pages deployment succeeded after that UI change: https://github.com/AION-2000/AIOClips-AI/actions/runs/43920669524

**Not yet verified:** an end-to-end Android website → authenticated cloud render → download workflow.

## 5. Outstanding requirements, in recommended order

### Phase 1 — Complete the honest mobile experience (next)
- Make the landing page clearly distinguish **Paste a reference URL**, **Upload authorized footage**, and **Create an original story**.
- Add usable original-story title, beats and duration controls with safe input validation.
- Show which actions work today and which need a connected service; never present fake generation as live.
- Add accessibility, loading/error states and responsive Android checks.

**Done when:** users can prepare a valid job on their phone and understand exactly what will happen.

### Phase 2 — Secure browser-to-cloud rendering
- Choose a secure authorization and dispatch mechanism. **Never put a GitHub personal access token in public JavaScript.**
- Design around GitHub Actions' limitations: workflow dispatch permissions, job quotas, public-repository visibility and artifact access.
- Add render status, failure feedback and a secure way to retrieve outputs.
- Do not put private footage, confidential scripts or customer data in public workflow inputs or artifacts.

**Done when:** an authorized user can submit a non-sensitive original story from Android and retrieve a real MP4 without manually navigating GitHub Actions.

### Phase 3 — Private media pipeline
- Deploy the FastAPI renderer behind HTTPS with proper authentication.
- Add private media upload, durable jobs, storage retention/deletion, quotas, logging and safe download links.
- Test the complete upload → highlight selection → render → download journey on Android.
- Investigate free-tier compute options honestly; **zero cost cannot be guaranteed** for sustained video processing.

**Done when:** licensed/owned footage can be securely edited from a phone without a local PC.

### Phase 4 — Better AI and creator quality
- Add transcript extraction and more accurate caption timing.
- Improve scene/audio/vision-based highlight ranking and user controls.
- Add templates, thumbnails, narration, preview quality controls and revision history.
- Evaluate results on authorized sample footage.

### Phase 5 — Production release
- Accounts and session management, persistent project history, observability, abuse prevention and security review.
- Optional publishing integrations only with authorized OAuth and explicit human approval.
- Performance, mobile accessibility and operational documentation.

## 6. Security, copyright and cost principles

- **Privacy:** never expose tokens, private uploads or confidential content in a public GitHub Pages app or public workflow.
- **Rights:** clip only footage the user owns, has permission to edit, or can access through an authorized integration. A URL alone is not permission.
- **Honest status:** do not label URL validation, static mockups or audio-energy heuristics as full AI video understanding.
- **Human control:** review footage, factual accuracy, captions and rights before any publication.
- **Cost:** GitHub Pages and qualifying public-repository Actions runs can support a no-cost prototype under applicable limits, but they are not an unlimited free private rendering platform.

## 7. Decisions still open

1. **Link workflow:** should URL entry be reference-only by default, with an optional authorized media upload alongside it? (Recommended: yes.)
2. **Cloud infrastructure:** secure backend hosting and storage choice for private videos.
3. **Product scope:** original-story Shorts first, or private uploaded-footage clipping first.
4. **Authentication:** single-owner private studio initially versus multi-user accounts later.

## 8. Source of truth

- [Repository README](../README.md)
- [Architecture](ARCHITECTURE.md)
- [Roadmap](ROADMAP.md)
- [Free batch-rendering guide](FREE_BATCH_RENDERING.md)
- [Security policy](../SECURITY.md)
- [Live Pages preview](https://aion-2000.github.io/AIOClips-AI/)

**Bottom line:** We have a deployed static UI, a locally functional FastAPI/FFmpeg studio, passing automated tests and one verified cloud-rendered MP4. We **do not yet** have a fully connected public link-to-Shorts application. The immediate goal is a secure, genuinely usable Android-first workflow that bridges these parts without overstating capabilities or exposing private media.
