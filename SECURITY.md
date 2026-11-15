# Security notes

This is not yet a production-ready application.

- URL validation is preflight only, not a downloader or full SSRF defense.
- A future downloader must validate every resolved address, pin the connection, revalidate redirects, enforce egress restrictions, and limit duration and response sizes.
- Run FFmpeg and media parsers in non-root, resource-limited containers.
- Enforce authentication and authorization for every asset and render.
- Store media privately and keep API tokens, passwords and .env files out of Git.
- Respect content ownership, licensing, and platform access restrictions.
