<div align="center">
  <img src="assets/brand/hero.svg" alt="AIOClips AI — Find the moment. Shape the story." width="100%" />

  <br />

  **A private, rights-aware studio for turning authorized footage and independently written stories into vertical video.**

  <a href="https://github.com/AION-2000/AIOClips-AI/actions/workflows/backend-tests.yml"><img alt="Backend checks" src="https://github.com/AION-2000/AIOClips-AI/actions/workflows/backend-tests.yml/badge.svg" /></a>
  <img alt="Python 3.11" src="https://img.shields.io/badge/Python-3.11-2C5166?style=flat-square&logo=python&logoColor=white" />
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-API-11856E?style=flat-square&logo=fastapi&logoColor=white" />
  <img alt="FFmpeg" src="https://img.shields.io/badge/FFmpeg-rendering-2C5166?style=flat-square" />
  <img alt="Status: Alpha" src="https://img.shields.io/badge/Status-Alpha-E8B04E?style=flat-square" />

  <br /><br />

  <a href="https://aion-2000.github.io/AIOClips-AI/"><strong>🌐 LIVE PREVIEW</strong></a> · <a href="https://github.com/AION-2000/AIOClips-AI/actions/workflows/batch-original-story.yml"><strong>☁️ CLOUD RENDERER</strong></a>

  <br />

  [**Get started**](#quick-start) · [**Explore capabilities**](#capabilities) · [**Architecture**](docs/ARCHITECTURE.md) · [**Roadmap**](docs/ROADMAP.md) · [**Security**](SECURITY.md)

</div>

---

## Live links

| Experience | Link | Current status |
| :--- | :--- | :--- |
| **Android-first website** | **[Open AIOClips AI ↗](https://aion-2000.github.io/AIOClips-AI/)** | Public interface connected in code to the Render original-story API; real-phone acceptance pending |
| **Cloud video rendering** | **[GitHub Actions batch renderer ↗](https://github.com/AION-2000/AIOClips-AI/actions/workflows/batch-original-story.yml)** | Working original-story batch render; requires authorized GitHub workflow access |
| **Original-story HTTPS renderer** | **[Render service health ↗](https://aioclips-original-story.onrender.com/v1/health)** | Live service on Render Free; single-owner token required for jobs |

> **Current release:** GitHub Pages now offers a real original-story form wired to the separately hosted Render API. Render reports its service as live, and automated FFmpeg tests pass. **End-to-end testing on a physical Android phone is still pending.** Paste-URL mode is reference-only; authorized footage upload is not yet connected to the public site.

## Built for moments, not timelines

AIOClips AI is a personal production workspace for discovering compelling segments in footage **you can legally reuse** and exporting them as polished 9:16 drafts. When a third-party video is only a reference, a separate **Original Story** workflow generates new graphics from independently written material—without downloading or reusing that video's frames or audio.

> [!IMPORTANT]
> **Development alpha, not a production SaaS or copyright-clearing tool.** The GitHub Pages [site](https://aion-2000.github.io/AIOClips-AI/) has an original-story creator linked to a single-owner Render API. A backend owner token must be entered in memory to generate MP4. The existing footage upload/edit API is still a **separate local-only studio**.

### Three creative paths

| | **Highlight Studio** | **Original Story Studio** |
| :--- | :--- | :--- |
| **Starting point** | Original or licensed video file | Independently verified facts and newly written story beats |
| **Output** | Vertical clip based on authorized footage | Newly generated geometric visuals |
| **Creative layers** | Headline, animated captions, optional voiceover | Original title, animated captions, optional voiceover |
| **Source permissions** | Footage and audio reuse rights required | Reference link is never imported or downloaded |
| **Review** | Human rights and content review | Human facts, originality and publication review |

## Music to Video (new)

Open the **[Android-friendly website](https://aion-2000.github.io/AIOClips-AI/)** and select **Music to Video**. Upload your own or commercially licensed MP3/WAV/M4A, record the commercial-use rights category, license name and proof URL, then generate a beat-synced MP4 with optional waveform visualization. The backend writes a private per-job rights manifest and credits files, exposes progress stages, and automatically removes expired files.

- **Always usable without external AI/stock keys:** FFmpeg audio duration, BPM estimate and energy analysis, free rule-based mood/colors/scenes, generated animated gradients, crossfade and audio normalization. Final file presets are 1080×1920 and 1920×1080 (composed at lower internal resolution and upscaled).
- **Optional hosted integrations:** Anthropic `claude-sonnet-5-5` scene planning with server-only `ANTHROPIC_API_KEY`; Pexels and Pixabay licensed stock lookup with server-only keys and per-scene credits. API calls and paid model tokens may incur charges.
- **AI music generation is deliberately disabled.** The pluggable provider interface is ready, but no commercial-use-verified free audio generator is configured. Use the upload option.
- **Known limitations:** approximate BPM/lyrics timing, no automatic vocal transcription, Render Free memory/CPU and ephemeral 24-hour-best-effort storage. Mobile live end-to-end acceptance is still pending. No automatic publication.

See the **[Music to Video setup and licensing guide](docs/MUSIC_TO_VIDEO.md)** for exact Android instructions, environment variables, source credits and limits.

## Capabilities

| Capability | State | What it actually does |
| :--- | :---: | :--- |
| Private, mobile-friendly studio | ✅ Implemented | Browser UI served by the backend with bearer-token API access |
| Local video upload | ✅ Implemented | Validates playable media, duration and file size |
| Moment suggestions | ✅ Heuristic | Uses audio energy; scene-cut fallback for silent footage |
| Short-form rendering | ✅ Implemented | FFmpeg 1080 × 1920 output with blurred backdrop and headline |
| Animated subtitles | ✅ Implemented | Karaoke-style ASS captions with estimated pacing |
| AI narration | 🔑 Optional | Speech API integration; needs a separately configured API key and credits |
| Original Story mode | ✅ Implemented | Generates graphics from your verified, independently written text |
| YouTube URL recognition | ✅ Implemented | Validates links only; **does not download video** |
| Automatic goal/event understanding | ◻ Planned | No vision-based semantic event recognition yet |
| Automatic link-to-video pipeline | ◻ Planned | YouTube links are reference-only; the hosted API accepts authorized uploaded files, not URL downloads |
| Frame-accurate caption alignment | ◻ Planned | Captions currently use estimated timing |
| YouTube OAuth publishing | ◻ Planned | No direct upload or automatic publishing |
| Original-story cloud deployment | ✅ Service live | Render Free hosts isolated original-story API; actual Android browser video generation needs acceptance testing |
| **Authorized footage upload & clipping** | ✅ Hosted beta | Upload an authorized file (including licensed third-party footage), review audio-energy / scene-cut suggestions, trim, add captions and render a 540×960 MP4. 40 MiB / 3-min beta limits; Android acceptance pending |
| **Music to Video** | ✅ Tested in CI | Rights-gated upload → beat/energy analysis → offline or Anthropic theme → stock or FFmpeg visuals → MP4; real Android acceptance pending |

<details>
<summary><strong>What the app currently looks like</strong></summary>

The older footage-editing studio is in [`backend/app/studio.html`](backend/app/studio.html) and [`backend/app/studio.js`](backend/app/studio.js). The public [GitHub Pages studio](https://aion-2000.github.io/AIOClips-AI/) now submits original text jobs to the separate authenticated [`backend/app/original_api.py`](backend/app/original_api.py) service. No third-party footage is fetched.

</details>

## Workflow

```mermaid
flowchart LR
    A["Choose source"] --> B{"Reuse rights?"}
    B -->|"Owned / licensed"| C["Upload video"]
    B -->|"Reference only"| D["Write verified original story"]
    C --> E["Suggest moments"]
    E --> F["Select segment"]
    D --> G["Generate fresh graphics"]
    F --> H["Captions + optional AI voice"]
    G --> H
    H --> I["Render vertical MP4"]
    I --> J["Human review"]
    J --> K["Download draft"]
```

**No automatic social publishing occurs.** Video source rights, script originality, factual correctness, and platform eligibility remain the publisher's responsibility.

## Quick start

### Requirements

- Docker, or Python 3.11 with FFmpeg/FFprobe installed
- A private `STUDIO_ACCESS_TOKEN` for the API
- Optional: `OPENAI_API_KEY` for AI narration (**never expose it in client code**)

### Option A — Docker

From the repository root:

```bash
docker build -t aioclips-studio .

docker run --rm \
  --name aioclips \
  -p 127.0.0.1:8000:8000 \
  -e STUDIO_ACCESS_TOKEN="replace-with-a-strong-random-token" \
  -v aioclips-data:/data \
  aioclips-studio
```

The Docker image starts the focused **original-story and authorized-footage API** on **http://localhost:8000/v1/health**. For the Android website, use the hosted HTTPS endpoint and enter the token only into the browser's password field. The older private footage-editing studio can still be run separately via `uvicorn app.server:app` from `backend/`.

### Option B — Python development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt

export STUDIO_ACCESS_TOKEN="replace-with-a-strong-random-token"
cd backend
uvicorn app.server:app --reload
```

For Windows PowerShell, activate with `.venv\Scripts\Activate.ps1`, set the token using `$env:STUDIO_ACCESS_TOKEN="..."`, and ensure `ffmpeg` and `ffprobe` are on your PATH.

Visit **http://127.0.0.1:8000**. Developer API docs are available at **http://127.0.0.1:8000/docs**.

> [!NOTE]
> A Render Free HTTPS original-story API is deployed at [aioclips-original-story.onrender.com](https://aioclips-original-story.onrender.com/v1/health). Follow the [Android guide](docs/MOBILE_STUDIO_DEPLOYMENT.md) for token entry and a complete manual acceptance test. Free hosting sleeps, restarts and loses temporary files; it is **not** reliable production storage.

## Project layout

```text
AIOClips-AI/
├── assets/brand/             # Custom GitHub visual identity
├── backend/
│   ├── app/
│   │   ├── original_api.py   # Hosted private original-story API (540x960)
│   │   ├── server.py         # Local authorized-footage API
│   │   ├── studio.html/.js   # Mobile-friendly private editor
│   │   ├── clip_studio.py    # Licensed-footage workflow
│   │   ├── original_story.py # New visuals, no reference-footage reuse
│   │   ├── match_clips.py    # Audio-energy detection and FFmpeg export
│   │   ├── highlights.py     # Scene-cut candidates
│   │   ├── captions.py       # Animated ASS subtitles
│   │   ├── voice.py          # Optional AI speech
│   │   └── approval.py       # Review and publication eligibility rules
│   └── tests/                # Python tests and render smoke tests
├── docs/                     # Architecture, setup and product roadmap
├── .github/workflows/        # Backend tests and Pages preview
├── Dockerfile                # Non-root processing container
└── render.yaml               # Optional Render hosting blueprint
```

Read the [architecture documentation](docs/ARCHITECTURE.md) for boundaries, data flow and known production gaps.

## Engineering quality

Run tests locally:

```bash
python -m pip install -r backend/requirements.txt
cd backend
python -m pytest -q
```

GitHub Actions runs the backend test suite, including synthetic FFmpeg video-render checks. Passing tests validates the checked behaviors; it **does not** certify footage rights, public deployment, or end-to-end external AI availability.

## Responsible use

A watermark, crop, angle change, voiceover or caption track **does not** make unlicensed footage yours. AIOClips intentionally separates authorized footage edits from wholly original visual stories. Content ID claims, copyright strikes and platform monetization decisions cannot be guaranteed away.

Review [`SECURITY.md`](SECURITY.md) before exposing the service to the internet. Current limitations include in-memory jobs, local storage and a shared private token; production hosting needs stronger user/session management, quotas, observability and job persistence.

## Documentation

| Resource | Why it matters |
| :--- | :--- |
| **[Music to Video setup](docs/MUSIC_TO_VIDEO.md)** | Music upload, rights proof, audio analysis, Render configuration, credits, limitations |
| **[Android studio deployment](docs/MOBILE_STUDIO_DEPLOYMENT.md)** | Live backend, owner-token setup, usage, limits and test checklist |
| **[Authorized footage workflow](docs/AUTHORIZED_FOOTAGE_WORKFLOW.md)** | Upload, heuristic highlight selection, licensed third-party clipping, rights and free-tier limits |
| **[Project vision & progress](docs/PROJECT_VISION_AND_PROGRESS.md)** | Project vision, verified milestones and delivery backlog |
| [Architecture](docs/ARCHITECTURE.md) | Components, trust boundaries and real request flows |
| [Roadmap](docs/ROADMAP.md) | Prioritized delivery plan with acceptance criteria |
| [Deployment guide](docs/DEPLOYMENT.md) | Local development and hosting requirements |
| [Contributing](CONTRIBUTING.md) | Contribution and quality conventions |
| [Security](SECURITY.md) | Risk disclosure and deployment hardening |
| [Match clipping notes](docs/MATCH_CLIPS.md) | Audio-scene heuristics and authorized sources |

---

<div align="center">
  <sub><strong>AIOClips AI</strong> · Designed for original storytelling and responsible media workflows.</sub>
</div>
