# Authorized Third-Party Footage — Android Highlight Workflow

**Implemented in code, November 2026.** The new footage path is connected to the same single-owner Render backend as Original Story. It accepts **uploaded video files** whose reuse is authorized; it does **not** fetch or download YouTube, TikTok, Facebook, or other third-party video URLs.

## What "third-party" means

The footage may have been created by another person or organization. Before importing it, the owner must have a valid basis to edit and reuse it: an applicable license, explicit permission, a public-domain status, or a compatible Creative Commons license. Provide the source/rights evidence in the app. A self-declaration is **not** automated proof of legal rights. Review the terms, any required attribution, and intended publication jurisdiction yourself.

A public streaming URL is **not** a download entitlement. The Paste Reference URL mode validates YouTube links but does not import streams. No DRM bypasses or copyrighted-video ripping are implemented.

## Android workflow

1. Open https://aion-2000.github.io/AIOClips-AI/ in Chrome.
2. In **Connect your private renderer**, leave the HTTPS backend address as \`https://aioclips-original-story.onrender.com\`, and enter your server-held private owner token. The token is never embedded in the public website.
3. Select **Clip permitted footage**.
4. Choose an authorized MP4, MOV, WebM or MKV file stored on the phone. The free beta currently caps uploads at **40 MiB** and **3 minutes**.
5. Select the correct rights category, enter source/license evidence and confirm the right to edit.
6. Tap **Upload & analyze moments**. The server uses FFmpeg-based audio energy or scene cuts to produce timestamped candidate moments.
7. Select a candidate or edit start/end times. Add a new headline and your original on-screen commentary; confirm your publication permissions.
8. Tap **Render selected Short**. Monitor the job status, preview the returned **540×960** vertical MP4 and tap **Download edited MP4**.
9. Save the video promptly. Uploads/exports expire after about 30 minutes and can disappear sooner if Render Free restarts.

No social posting is performed. A generated clip must be reviewed for quality, permissions and accuracy.

## What the analysis does

**Available now:** audio RMS energy ranking; fallback to scene transition density for a silent video; optional manual in/out timestamps; real FFmpeg portrait rendering with blurred background, centered source image, title and captions.

**Not available yet:** semantic video understanding such as identifying goals, fouls, punchlines, emotions or key actions; transcript-based selection; automatic third-party URL ingestion; automatic rights verification; AI-powered source summaries; background processing of hours-long videos.

This is heuristic analysis, not a pretrained visual-language model. Short video clips can be selected manually in the meantime.

## New hosted API

All non-health endpoints require \`Authorization: Bearer <owner-token>\` and are accessible from the configured GitHub Pages origin:

- \`POST /v1/footage/uploads\`: multipart \`video\`, \`rights\`, \`rights_evidence\`, \`permission_to_edit\`. Returns an opaque \`asset_id\` and video duration.
- \`POST /v1/footage/{asset_id}/highlights\`: JSON \`{"seconds":15,"limit":5}\`. Returns \`moments\` with \`start\`, \`end\`, \`score\` and \`kind\`.
- \`POST /v1/footage/{asset_id}/clips\`: JSON \`start\`, \`end\`, \`headline\`, \`caption_script\` and \`permission_to_publish\`. Returns a job ID.
- \`GET /v1/story/jobs/{job_id}\`: shared authenticated job status for both original-story and footage clips.
- \`GET /v1/story/jobs/{job_id}/download\`: shared bearer-protected MP4 download.

The source file is stored temporarily under a generated opaque ID and is **not served publicly**. The server never receives a third-party URL for download.

## Security and infrastructure limits

- Free hosting is suitable for **small personal test clips**, not large-scale publishing. CPU, memory and disk are limited.
- MIME and FFprobe validation, 40 MiB upload limit, 180-second media duration limit, 60-second maximum exported clip, request limits, bounded render queue, fixed 540×960 output.
- Original footage and exports remain on temporary local server disk; completed jobs and expired uploads are automatically deleted on a schedule.
- Server-held owner token, HTTPS, one allowlisted browser origin, and no public GitHub Actions media artifacts.
- This is a single-owner prototype. No independent license verification, malware scanning, dedicated process sandbox, persistent job storage, or guaranteed service uptime. Do not upload sensitive footage.
- The new API tests create a **synthetic test video**, analyze it and render a real clip. Green CI does not replace manual testing on a real Android phone.

## Next version

After Android acceptance, add transcript-based segmentation (for supported speech), semantic event detection using a suitable video or multimodal model, smarter rankings, downloadable timelines and source provenance review. These would likely require additional cloud CPU/GPU resources and may not fit Render Free.
