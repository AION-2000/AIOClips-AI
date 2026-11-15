# AIOClips AI

A private, rights-aware video clipping studio. **Development alpha — not an automatic copyright-clearing service.**

## What works in the private backend

- Upload a video that you own or have permission to edit and publish (up to 700 MB; maximum four hours).
- Suggest high-audio-energy moments, with scene-change fallback for silent footage.
- Choose any start and end time, regardless of whether it is a football goal, gaming play, reaction, animal moment, tutorial moment or anything else.
- Render a vertical 1080×1920 MP4 with the entire source picture visible over a blurred background.
- Add animated karaoke-style captions. Timing is approximate, not forced-aligned.
- Optionally generate original spoken narration using OpenAI's speech API, if a paid API key is configured.
- Use a mobile-friendly private studio interface with bearer-token authentication and download exports.
- Run the API with FFmpeg inside a Docker container.

## Not yet done

- **YouTube links are parsed for reference only**. YouTube videos are not downloaded; a link is not proof of editing/publication rights. Upload a separately authorized original file.
- Goal or event identification by AI vision, automatically accurate commentary, word-perfect caption alignment and automated YouTube OAuth publishing are not complete.
- The GitHub Pages URL is an independent static prototype; **it does not run FFmpeg or the authenticated backend**.
- The private studio API must be hosted on a server; it is not live merely because the source was committed to GitHub.

## Run locally

Requires Docker.

```bash
docker build -t aioclips-studio .
docker run --rm -p 127.0.0.1:8000:8000 \
  -e STUDIO_ACCESS_TOKEN="replace-with-a-long-random-secret" \
  -e OPENAI_API_KEY="your-own-server-side-api-key" \
  -v aioclips-data:/data aioclips-studio
```

Open http://localhost:8000 and enter the configured studio token. `OPENAI_API_KEY` is optional if you leave narration empty.

For phone use outside your local network, deploy the Docker image to an HTTPS host with persistent storage and a private access token. `render.yaml` provides an optional paid hosting blueprint.

### API endpoints

- `GET /`: mobile-friendly private studio
- `GET /v1/health`: health check
- `POST /v1/links`: check supported YouTube link metadata; does **not** import footage
- `POST /v1/uploads`: upload a video file
- `POST /v1/moments`: suggested clip timestamps
- `POST /v1/renders`: queue authorized draft export
- `GET /v1/renders/{job_id}`: job status
- `GET /v1/exports/{job_id}`: download approved-source draft

All media endpoints require the `Authorization: Bearer <STUDIO_ACCESS_TOKEN>` request header.

## Security and copyright

Do not commit credentials, access tokens, media or AI-generated outputs. Copyright ownership, scope of licenses, music/audio rights and commercial reuse must be independently verified before publishing. **Adding AI narration, cropping or captions does not remove content ownership or guarantee zero copyright claims/strikes.** YouTube's reused-content monetization policy is separate from copyright permissions.

This alpha has in-memory jobs and local storage; use persistent queues, quotas, cleanup, rate limiting, monitoring, and an upload sandbox before offering it to other users.

See `docs/MATCH_CLIPS.md` and `SECURITY.md`.
