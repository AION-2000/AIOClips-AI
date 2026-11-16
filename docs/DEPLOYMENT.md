# Development and deployment

AIOClips consists of a **static prototype** and an independently hosted **private rendering service**. The GitHub Pages URL does not execute the backend.

## Local development

Install **Python 3.11** and **FFmpeg/FFprobe**. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
export STUDIO_ACCESS_TOKEN="use-a-random-secret"
cd backend
uvicorn app.server:app --reload --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r backend/requirements.txt
$env:STUDIO_ACCESS_TOKEN = "use-a-random-secret"
cd backend
uvicorn app.server:app --reload --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Provide the token in the studio UI. Verify <http://127.0.0.1:8000/v1/health>. API docs: <http://127.0.0.1:8000/docs>.

## Running tests

```bash
cd backend
python -m pytest -q
```

Integration tests generate synthetic video/audio using FFmpeg; they do not require third-party media.

## Docker

```bash
docker build -t aioclips-studio .
docker run --rm -p 127.0.0.1:8000:8000 \
  -e STUDIO_ACCESS_TOKEN="use-a-random-secret" \
  -v aioclips-data:/data \
  aioclips-studio
```

The Dockerfile installs FFmpeg and fonts, uses a non-root account, and stores media at `/data`. A persistent volume is essential because uploads/exports are saved locally.

## Environment

| Variable | Required | Purpose |
| --- | --- | --- |
| `STUDIO_ACCESS_TOKEN` | **Yes** | Private bearer token for all media API actions |
| `STUDIO_DATA_DIR` | No | Backend upload/export root; Docker default `/data` |
| `OPENAI_API_KEY` | Only for AI narration | Server-side speech API credential |
| `PORT` | No | Hosting port; Docker defaults to 8000 |

Never put secrets in source control, screenshots, browser local storage, or `render.yaml`. Use the host's secure environment-variable configuration.

## Render hosting

A [Render Blueprint](../render.yaml) is provided as a deployment example. It currently describes a Docker web service with persistent disk, and therefore may require a paid compute/disk plan. **Do not assume it is deployed.** The latest attempted creation did not provision the service because Render required payment information.

Before proceeding:

1. Review the current Render [compute plans](https://render.com/docs/compute-plans) and [disk pricing](https://render.com/docs/disks).
2. In Render, connect the repository and review the Blueprint plan **before** accepting charges.
3. Configure the private `STUDIO_ACCESS_TOKEN` and optional `OPENAI_API_KEY` in the service environment. Do not expose their values.
4. Ensure the persistent disk is mounted at `/data`.
5. Verify `GET /v1/health` returns `status: ok` and the mobile UI is reachable over HTTPS.
6. Upload a small video **you own**, render a Short, download it on your phone and confirm that video/audio play.
7. Validate restart behavior, access rejection, and storage limits before sharing the service.

### Operations warning

The MVP uses an in-memory job registry. Rendering jobs may be lost on restart, and generated files are not automatically cleaned up. The current shared token also lacks account-level isolation. Keep this service private and do not expose it as a multi-user product.

## Public preview

The separate [GitHub Pages preview](https://aion-2000.github.io/AIOClips-AI/) displays UI design only. It does **not** process uploaded videos or reflect the private backend's capabilities.

## Security preflight

Before accepting real users or valuable media, implement persistent jobs, storage retention rules, user identity, stricter resource quotas, secure media parsing and per-user access policies. See [SECURITY.md](../SECURITY.md) and [architecture](ARCHITECTURE.md).
