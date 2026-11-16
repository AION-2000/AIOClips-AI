# Security policy

> AIOClips AI is a development-alpha media application. The repository is **not yet production hardened**.

## Reporting a vulnerability

Please **do not publish exploitable vulnerabilities, private footage, or credentials** in a public GitHub issue. Use GitHub's private vulnerability reporting feature, if enabled for the repository, or contact the repository maintainer privately through an established contact method. Never email or post API keys or complete access tokens.

When reporting, include an affected commit or version, a safe reproduction procedure using synthetic media, impact, and recommended mitigations. Give the maintainer a reasonable opportunity to assess the issue before disclosing technical exploit details publicly.

## Current trust model

| Area | Current approach | Before multi-user production |
| :--- | :--- | :--- |
| Authentication | Single server-side bearer token | Individual identities, revocable sessions, role/asset ACLs |
| Uploads | Chunked size limit and FFprobe duration checks | Content screening, quota policies and a media sandbox |
| Video processing | FFmpeg subprocess arguments, non-root Docker image | CPU/memory caps, isolation, kill policies and malicious input fuzzing |
| Storage | Server-local private uploads and exports | Tenant separation, retention, encryption policies and object storage |
| Jobs | In-memory executor and status map | Durable, bounded queue with cancellation and retry |
| External links | HTTPS URL validation and allowlists | A hardened fetcher if direct ingestion is ever introduced |
| Secrets | Environment variables only | Managed secret storage and rotation |
| Publishing | Review required in domain policy | Durable signed approval history and connected enforcement |

## Deployment baseline

1. Use HTTPS and an up-to-date FFmpeg build.
2. Keep `STUDIO_ACCESS_TOKEN` secret and random; rotate it if exposed.
3. Keep `OPENAI_API_KEY` server-side only. Never commit or embed it in web assets.
4. Do not expose upload endpoints without authentication and rate limits.
5. Use persistent private storage for uploaded media; do not serve source files directly.
6. Limit video sizes, CPU, memory, execution times and network access.
7. Store no media you lack permission to process.
8. Avoid deploying a shared personal token as an internet-facing, multi-user authentication system.

## Media source safety

A YouTube URL is only a reference. The app does **not** download YouTube video streams and intentionally avoids DRM/Content ID circumvention. Authorization to view a video does not prove the right to reuse it. A watermark, filter or voiceover cannot establish video ownership.

The `url_safety.py` validator is a preflight check, **not a complete SSRF defense**. Any future media downloader must validate DNS responses and every redirect, pin outbound addresses, reject private/reserved IP ranges, enforce egress restrictions, and bound response bytes and time.

## Supported release status

This repository currently describes an **alpha**, with no guaranteed security support or published security-service-level agreement. Use it for private development with test or authorized material until the production controls above are complete.
