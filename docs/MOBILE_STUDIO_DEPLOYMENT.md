# Android Original-Story Studio — Deployment and Test Guide

**Status (2026-11-17):** GitHub Pages and the Render Free Docker service host **Original Story** and **authorized footage** workflows. CI verifies both real FFmpeg render paths. **Physical Android-browser submission and download still require acceptance testing**.

- **Web app:** https://aion-2000.github.io/AIOClips-AI/
- **Private renderer HTTPS root:** https://aioclips-original-story.onrender.com
- **Public health endpoint:** https://aioclips-original-story.onrender.com/v1/health
- **Render dashboard:** https://dashboard.render.com/web/srv-dbtk5gmi0phs73djqke0
- **GitHub CI:** https://github.com/AION-2000/AIOClips-AI/actions/workflows/backend-tests.yml

## What is live, and what is not

| Mode | Status | Meaning |
| --- | --- | --- |
| Create original story | Connected code, server provisioned; phone acceptance pending | Sends original title + 1–8 beats over HTTPS to an authenticated FFmpeg renderer |
| Paste YouTube reference | Live browser-only validation | Checks URL syntax; does not download, summarize or clip videos |
| Upload authorized or licensed third-party footage | Hosted beta (phone acceptance pending) | Mobile upload, audio/scene highlight suggestions, timestamp selection and MP4 export; 40 MiB/3-min file limits |

## Licensed third-party footage workflow

The site also has **Clip permitted footage**. Upload a video file for which you have a valid reuse basis, describe the license/permission source, and confirm edit permission. The app suggests high-audio-energy or scene-change segments; select one, add a new title and commentary and render a 540×960 MP4 using the same authentication and status/download endpoints.

See [Authorized footage workflow](AUTHORIZED_FOOTAGE_WORKFLOW.md) for detailed instructions, resource limits and legal/security boundaries. **YouTube video links are still reference-only and are never downloaded.**

## Security setup (single owner)

The **server-only** secret environment variable is named **STUDIO_ACCESS_TOKEN**. The value must be a random token **at least 32 characters** long. It is **not** committed to GitHub, placed in HTML/JavaScript, added to workflow inputs or sent as a URL query parameter.

The browser asks for the token through a password field. It remains in that page's memory and is used as a bearer header over HTTPS. It is **not stored in localStorage, sessionStorage or cookies**. Reloading the page clears it. This is a single-owner prototype, not a full accounts/login system.

To rotate the token:
1. Open [your Render service dashboard](https://dashboard.render.com/web/srv-dbtk5gmi0phs73djqke0).
2. Open **Environment**.
3. Find **STUDIO_ACCESS_TOKEN**; choose **Edit** or **Add Environment Variable** if absent.
4. Set a long newly generated random value (for example, generate locally with the command below), then select **Save, deploy** / **Save and deploy**.
5. When deployment is live, enter the *new* value into the private website passphrase field. The old token will no longer work.

Generate a new token on a private terminal:
\`\`\`bash
python -c "import secrets; print(secrets.token_urlsafe(36))"
\`\`\`

Never paste the token in a public issue, GitHub Actions input, shared screenshot or public repository file.

## Use on Android

1. Open https://aion-2000.github.io/AIOClips-AI/ in Chrome.
2. Keep **Create original story** selected.
3. Check that **Backend HTTPS URL** shows \`https://aioclips-original-story.onrender.com\`.
4. Tap **Check connection**. A Render Free service may take roughly a minute to wake up after sleeping; try again if needed.
5. Enter your **owner passphrase** in the password field. The site will never remember it after the tab is reloaded.
6. Enter a title and **one story beat per line** (1–8 beats, each up to 180 characters).
7. Choose **3–10 seconds per beat**; output is always **540×960**, portrait, H.264 MP4.
8. Check both fact/originality declarations, then tap **Generate MP4**.
9. Keep the tab open as it shows submission, rendering and retrieval status. When a real MP4 arrives, play it in **Your Short**, then tap **Download MP4**.
10. Downloads expire from the server after ~30 minutes (or may disappear sooner on a free-service restart). Download locally.

**Troubleshooting:** A 401 response means the passphrase is wrong; a 503 response means Render does not have a valid secret configured; a 429 response means request/queue limits were reached; a network/CORS error suggests the service is asleep, unavailable or the origin/URL is wrong. An error in the output means server-side rendering failed; inspect Render logs.

## Technical contract

- \`GET /v1/health\` — public minimal health result and \`configured\` boolean.
- \`POST /v1/story/jobs\` — bearer token; JSON:
\`\`\`json
{
  "title": "How it started",
  "beats": ["The beginning.", "The discovery.", "The takeaway."],
  "seconds_per_beat": 3,
  "facts_verified": true,
  "independently_written": true
}
\`\`\`
- \`GET /v1/story/jobs/{job_id}\` — bearer token; returns \`processing\`, \`ready\` or \`error\`.
- \`GET /v1/story/jobs/{job_id}/download\` — bearer token; sends actual MP4 bytes, not a redirect to a public artifact.
- JSON rejects unknown fields and invalid lengths; text control characters are rejected.
- CORS only allows \`https://aion-2000.github.io\`; browsers send \`Authorization\` with no cookies.
- Per-peer authentication and creation rate limits, one active FFmpeg worker, maximum two queued/running jobs.
- Temporary job metadata is in memory; the janitor deletes completed files after \`STORY_TTL_SECONDS\` (default 1800). Free-tier restarts lose all temporary state and media.
- Output: no external source video, soundtrack, downloaded media, external AI calls or social publishing.

## Local reproduction

Prerequisites: Python 3.11+, FFmpeg and FFprobe.

\`\`\`bash
git clone https://github.com/AION-2000/AIOClips-AI.git
cd AIOClips-AI
python -m pip install -r backend/requirements.txt
python -c "import secrets; print(secrets.token_urlsafe(36))"
\`\`\`

Copy the new random token into the server's private environment. On Bash:

\`\`\`bash
export STUDIO_ACCESS_TOKEN="paste-your-generated-token-here"
cd backend
python -m uvicorn app.original_api:app --host 127.0.0.1 --port 8000
\`\`\`

On Windows PowerShell, from the repository root:

\`\`\`powershell
$env:STUDIO_ACCESS_TOKEN = "paste-your-generated-token-here"
cd backend
python -m uvicorn app.original_api:app --host 127.0.0.1 --port 8000
\`\`\`

From a second shell, use \`curl\` with a token you supply through a private environment variable; never publish the commands with your actual token.

\`\`\`bash
curl -f https://aioclips-original-story.onrender.com/v1/health
cd backend
python -m pytest -q
\`\`\`

For Docker:
\`\`\`bash
docker build -t aioclips-original .
docker run --rm --name aioclips-original -p 127.0.0.1:8000:8000 -e STUDIO_ACCESS_TOKEN="paste-your-generated-token-here" aioclips-original
\`\`\`
Using a token directly in a shell command may put it in shell history or process metadata; for higher security, pass a private environment file that is **not committed to Git** instead.

## CI and acceptance criteria

Automated tests cover authentication, invalid payloads, CORS, rate limits, expiry, JavaScript syntax, DOM controls, and a **real 540×960 FFmpeg MP4**. The CI run verifies code on Linux, not the live Render service.

**Still to verify personally on Android:** open the website → Check connection → submit a short → observe \`ready\` → preview MP4 → download/open MP4 from Android Downloads. This exact cross-device test cannot be claimed completed by CI alone.

## Hosting limitations and pricing

Render Free has 512 MB RAM, sleeps after inactivity, provides ephemeral disk only and has service-hour and bandwidth limits. It is suitable for a personal prototype, **not** a durable production video processor. Long renders, free-tier quota exhaustion and service restarts can break jobs; there is no uptime guarantee. Pricing can change; see https://render.com/docs/free.

Do not enter confidential customer footage, private third-party scripts or credentials into public GitHub workflows. The renderer's temporary output is protected by the owner token, but this remains a single-owner beta and needs further operational security review before handling highly sensitive work.
