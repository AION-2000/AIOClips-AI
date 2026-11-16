# Music to Video — Android setup and implementation

**Status:** Music to Video was added to the existing AIOClips AI frontend and FastAPI backend on 17 November 2026. Automated tests include a real FFmpeg MP4 render. Real-device Android upload/render/download on the deployed Render Free service still requires acceptance testing.

## Start from Android (no PC)

1. Open **https://aion-2000.github.io/AIOClips-AI/** in Chrome.
2. In the **Connect your private renderer** section, keep **https://aioclips-original-story.onrender.com** and enter the **single-owner passphrase** already configured in the Render service. It remains in the browser tab's memory and is not saved.
3. Tap **Music to Video** (fourth tab).
4. Select an **MP3, WAV or M4A** you own or can legally use commercially. Default limit is **12 MiB and 90 seconds**, configurable on the server.
5. Select one of four music rights categories, supply the **license/plan name and HTTPS proof link**, and check the rights declaration. The job will refuse to start without all three. These details are retained in the authenticated job's \`manifest.json\`.
6. Optionally add generic visual keywords, your own licensed lyric text, output orientation, visualizer and stock/AI-theme preferences.
7. Tap **Generate Music Video**. Follow \`queued → analyzing → theming → fetching_visuals → rendering → ready\`; if it fails, a readable error appears.
8. Review the video, suggested title/description/hashtags, and **download both the MP4 and source-credits text**. Post manually; no automatic uploads or account connections.

### Upload mode is the default; AI music generation is disabled

Music generation has a \`MusicGenerationProvider\` interface in \`backend/app/music/music_provider.py\`, but **no provider is registered**. We could not confidently identify a *free music-generation provider whose applicable license unambiguously authorizes commercial usage of all generated audio*. No provider claims are made, and the UI disables that option. Upload an authorized existing track instead. A free API key or free tier alone does **not** confer commercial reuse rights.

The feature **does** use Anthropic's \`claude-sonnet-5-5\` for *visual theme planning* when a paid \`ANTHROPIC_API_KEY\` is configured. This does **not** generate music. With no key, it uses free local rules based on beat tempo and energy. See [Anthropic's model IDs](https://platform.claude.com/docs/en/models/overview).

## Analysis and results

- Audio is probed and decoded with FFmpeg at low sample rate. RMS energy, an onset-energy autocorrelation estimate of BPM, estimated beat timestamps and one-second energy curve are returned. **Beat detection is approximate**, especially for quiet, irregular or spoken music.
- \`theme_planner.py\` returns a validated mood, palette, 1–8 beat-aligned scenes, title, description and hashtags. The optional Anthropic call is server-side and may incur charges; API failures fall back to the free rules. Supplying lyric text with AI theme enabled sends those lyrics to Anthropic.
- **Automatic transcription is not enabled** on the Free server. The optional captions field takes lyrics the user supplies and is only *approximately timed*. Using \`faster-whisper\` would need a separate resource budget.
- \`visual_fetcher.py\` prefers licensed Pexels/Pixabay stock videos when you add API keys. It downloads at most **two provider clips per job** within a fixed bounded size, records each creator/source/license in \`credits.json\` and \`credits.txt\`, and uses FFmpeg gradients for remaining or unsuccessful scenes. No external API keys are required for a valid MP4.
- \`renderer.py\` makes beat-aligned cuts, FFmpeg crossfades, animated gradient backgrounds, a consistent color grade, optional reactive waveform, optional approximate captions and loudness normalization.
- Presets produce **1080×1920 portrait** and **1920×1080 landscape** H.264 MP4s. To fit free-host constraints, video is composed at **360×640 / 640×360** and upscaled. These are correct output dimensions, **not native Full-HD detail**.
- Files and rights manifests are **private to the single-owner API** and scheduled for deletion after **24 hours**. Render Free may erase them much sooner when the service spins down or redeploys.

## Server environment variables (Render dashboard)

Open the existing [Render web service](https://dashboard.render.com/web/srv-dbtk5gmi0phs73djqke0), select **Environment**, then add variables under **Environment Variables**. Choose the option to save and deploy. Do not paste keys into GitHub Pages JavaScript, public CI inputs, issues, source files or screenshots.

| Variable | Purpose | Required |
| --- | --- | --- |
| \`STUDIO_ACCESS_TOKEN\` | Existing strong private owner passphrase (32+ characters) | **Yes**, already set for original-story API; do not replace unless rotating |
| \`MUSIC_MAX_MB\` | Audio upload limit (1–30 MiB), default \`12\` | No |
| \`MUSIC_MAX_SECONDS\` | Audio length limit (5–180 sec), default \`90\` | No |
| \`ANTHROPIC_API_KEY\` | Optional paid Claude Sonnet 5.5 visual theme planner | No |
| \`PEXELS_API_KEY\` | Optional licensed Pexels video search | No |
| \`PIXABAY_API_KEY\` | Optional licensed Pixabay video search | No |
| \`STORY_DATA_DIR\` | Existing private temporary data directory; music jobs are stored in its \`music/\` child | No |

### Where to get optional keys

- **Anthropic:** Open [Claude Console](https://console.anthropic.com/), sign in, add API access/billing as required, then create an API key. Add it only to Render \`ANTHROPIC_API_KEY\`. It is **not free** to use in general.
- **Pexels:** Sign in to [Pexels API](https://www.pexels.com/api/), request an API key, then add it to Render \`PEXELS_API_KEY\`. Review [Pexels license](https://www.pexels.com/license/) and [API guidelines](https://www.pexels.com/api/documentation/). In particular, credit contributors where possible; do not simply redistribute unaltered stock content.
- **Pixabay:** Sign in to [Pixabay API](https://pixabay.com/api/docs/), copy your API key, then add it to Render \`PIXABAY_API_KEY\`. Review the [Pixabay license](https://pixabay.com/service/license-summary/), rate limits and source crediting terms. Credits are always recorded in each job when footage is used.

All three are **optional**; the no-key path still performs audio analysis, plans local animated scenes and renders a real MP4.

## New API (authenticated)

All requests require the existing \`Authorization: Bearer <STUDIO_ACCESS_TOKEN>\` header:

- \`GET /v1/music/config\` — safe configuration, upload limits and currently available generation providers.
- \`POST /v1/music/jobs\` — multipart audio plus \`rights\`, \`license_name\`, \`proof_link\`, \`rights_confirmed\`, style/lyrics and output settings. Returns job ID and 202.
- \`GET /v1/music/jobs/{id}\` — staged status, audio stats, sanitized theme and finished metadata.
- \`GET /v1/music/jobs/{id}/download\` — bearer-protected video download, only when ready.
- \`GET /v1/music/jobs/{id}/credits\` — bearer-protected credits text, only when produced.
- \`GET /v1/music/jobs/{id}/manifest\` — private JSON showing original rights proof, source information and processing status.
- \`POST /v1/music/generate\` — currently 501, explicitly explaining that no commercial-use-verified free music generation provider is configured.

The license proof and any potential personal details in the manifest **do not appear in public artifacts**.

## Tests and local development

This adds files under \`backend/app/music/\`, not a replacement of existing services:

- \`audio_analyzer.py\`, \`theme_planner.py\`, \`visual_fetcher.py\`,
  \`beat_editor.py\`, \`renderer.py\`, \`job_manifest.py\`,
  \`music_provider.py\` and \`api.py\`.
- \`backend/app/original_api.py\` only mounts the new router at the bottom.
- \`backend/tests/test_music_modules.py\`, \`backend/tests/test_music_api.py\` verify the rights gate, job status, manifest, beats, themes, credits, FFmpeg command builder and actual H.264 export.

To run the same tests on a computer (not required for Android):
\`\`\`bash
python -m pip install -r backend/requirements.txt
cd backend
python -m pytest -q
\`\`\`

A Docker host also needs FFmpeg and FFprobe. The existing Dockerfile and GitHub Actions backend CI already provide FFmpeg. **GitHub Actions runs tests and the original-story text-only batch smoke workflow. It does not receive private audio, licensed tracks, API keys, or music jobs**. Real Music to Video jobs run on the private FastAPI host (Render).

## Limitations and safe publishing

- **Render Free** is 512 MB RAM with shared CPU, sleeps after ~15 minutes idle, and has an ephemeral disk. Files can disappear on sleep or restart regardless of the 24-hour TTL. Large uploads, 90-second clips, multi-scene crossfades and full-resolution encoding may fail under resource limits. A paid CPU instance/worker and persistent private storage would be needed for reliable long videos. See [Render free limits](https://render.com/docs/free).
- There is no guaranteed free AI generation: Anthropic may cost money and free stock APIs have rate limits. With stock failures or no matches, the generator uses procedural visuals.
- Stock footage can have third-party brand, model, property or other rights restrictions. Review source clips and licenses before publishing; provider labels alone do not guarantee commercial suitability.
- Lyrics, recording, samples, sync rights and distribution permissions are your responsibility. The rights dropdown is a required declaration, **not a verification service**.
- No pitch shifting, mirroring, copyright-detection evasion, automatic publication or upload to social networks is provided.
- YouTube can require disclosure of realistic altered/generated content, including certain AI music. See [YouTube AI disclosure](https://support.google.com/youtube/answer/14328491). YouTube monetization policy restricts mass-produced or repetitive near-identical content; review videos and vary the creative substance. See [YouTube channel monetization policies](https://support.google.com/youtube/answer/1311392).

**Next verification milestone:** From a real Android browser submit a short synthetic/licensed audio file, see phase-by-phase status, preview and download the MP4 and credits. A green CI run alone cannot establish that Render Free has sufficient resources for your actual tracks.
