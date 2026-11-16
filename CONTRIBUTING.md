# Contributing to AIOClips AI

Thanks for helping build a thoughtful, secure private media studio. The project is in alpha, so reliability and an honest feature scope are more important than adding untested integrations.

## Principles

- Treat footage, voices, music and other source media as rights-managed assets. Do not add workflows designed to bypass DRM, Content ID or ownership checks.
- A reference link alone does not permit downloading or redistributing its contents.
- Avoid claiming features are ready when only a stub, prototype or unit test exists.
- Keep credentials, test media and API tokens out of commits.
- Aim for concise, accessible mobile-first controls and predictable failure messages.

## Development checklist

1. Create a focused branch from `main`.
2. Set up Python 3.11, FFmpeg and dependencies according to [the development guide](docs/DEPLOYMENT.md).
3. Add tests for the intended behavior, including negative or boundary cases.
4. Run `cd backend && python -m pytest -q`.
5. For changes to rendering, test with generated synthetic media and report FFmpeg configuration.
6. Update the README, architecture or roadmap if interfaces, security assumptions or capabilities change.
7. Open a pull request using the repository's template.

## Project conventions

- **Backend:** type hints for public functions, bounded input validation, meaningful errors, no unchecked shell execution.
- **Security:** no secret-bearing client parameters, no request-based file path construction, no uncontrolled third-party media imports.
- **Rendering:** output MP4s should be portable (`yuv420p`, H.264/AAC where applicable) and verify actual streams with FFprobe.
- **Frontend:** keyboard-accessible controls, touch-friendly layout and clear in-progress/error/success states.
- **Docs:** differentiate current behavior, planned functionality and deployment status.
- **Testing:** prefer fast unit tests plus a small, deterministic real-FFmpeg integration test.

## Reporting issues

Use the bug report or feature request issue templates. Remove API keys, personal footage, private URLs and any personally identifying information from logs or screenshots. For security-sensitive discoveries, follow [SECURITY.md](SECURITY.md) rather than opening a public issue.

## License

No public license is declared at this time. This repository is **not** automatically open source for unrestricted reuse. Contact the repository owner about rights to reuse, distribute or contribute substantive code before doing so.
