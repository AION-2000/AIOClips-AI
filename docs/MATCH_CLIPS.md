# Match clips workflow (in development)

The product is shifting from strategy explainers to footage-based match highlights.

## Desired phone workflow
1. Paste a **licensed or personally owned match recording link** (or upload a recording).
2. The service imports the authorized recording.
3. Audio energy analysis proposes candidate exciting moments; it **does not know which moments are goals**.
4. A future goal verification stage will cross-check timestamps with match event data and/or a vision model.
5. Render each selected segment to 1080x1920 with centered footage, blurred vertical backdrop and headline.
6. Add synthesized voiceover and animated word-level captions (not yet implemented).
7. Preview, edit, approve and publish via authenticated YouTube integration (not yet implemented).

## Current implementation
`backend/app/match_clips.py` provides:
- FFprobe duration
- FFmpeg audio-energy candidate selection
- Vertical short rendering with a headline and optional pre-existing narration audio

It requires installed FFmpeg/FFprobe and an accessible **local video file**. There is **no hosted processing API or working paste-link UI yet**.

## Copyright and platform constraints
A match link does not confer permission to reuse footage. Do not use protected broadcast video without permission. AI voiceovers, cropping and captions do not remove copyright or reused-content risks and cannot guarantee YouTube monetization or avoid restrictions.

## Engineering priorities
- Authenticated backend, bounded uploads and allowlisted direct-media import with SSRF protection
- Jobs, storage, and status/progress reporting
- Goal timestamp verification
- Licensed voice synthesis and timed animated captions
- Preview, explicit approval and YouTube OAuth upload
- Security tests, rate limits, quotas, and deployment
