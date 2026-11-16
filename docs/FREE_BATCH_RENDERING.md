# Free cloud batch-rendering prototype

This workflow uses GitHub-hosted Actions runners to produce an original 9:16 MP4 **without an always-on server**. It is a manual, Android-friendly prototype, not a hosted upload-and-edit application.

## Use from Android

1. Sign in to GitHub and open [AIOClips AI Actions](https://github.com/AION-2000/AIOClips-AI/actions/workflows/batch-original-story.yml).
2. Choose **Run workflow** on the `main` branch (enable **Desktop site** in Chrome if necessary).
3. Enter an original title, and a JSON array of 1-8 original story beats, e.g. `["The opening idea.","What happened next.","The takeaway."]`.
4. Select 3-10 seconds per beat. Check the confirmation **only if the text is original, verified and non-sensitive**.
5. Click **Run workflow**. Open the completed run and download the MP4 from **Artifacts**. GitHub may package it as a ZIP; extract it on Android.

The generated video is 540×960 (9:16), with procedural graphics and timed captions. It has **no voiceover**, no imported footage, and no automatic publication. The existing backend supports richer rendering separately.

## Privacy and security boundaries

- **The repository is public.** Never enter private video, unpublished scripts, names, credentials, customer material, private URLs, or personal data into workflow inputs.
- Workflow input text may be accessible in workflow metadata or logs. The generated artifact is **not a secure private vault**. Artifact retention is one day, but retention does not guarantee erasure of copies or caches.
- No external video downloads, arbitrary commands, untrusted file paths, or user-provided shell scripts are accepted.
- `GITHUB_TOKEN` has only `contents: read` permissions, checkout does not persist credentials, and no OpenAI API key is used.
- The manual confirmation is a declaration, **not** a legal or factual verification mechanism.
- Public repo workflows are not an authenticated multi-user job submission API. Only authorized GitHub users can manually dispatch workflows.

## Costs and limitations

GitHub-hosted standard runners are generally free for public repositories under GitHub's current policy and fair-use restrictions. Confirm your account's current Actions policy and limits before heavy use. This is not a guaranteed unlimited free rendering service.

This design deliberately does **not** put private video in Git, workflow inputs, artifacts, or a publicly accessible URL. Private uploads and browser-based one-click submission require a separate authenticated upload/storage backend, which is not included.

## Acceptance test

Run the workflow with the example beats, verify the job succeeds, download the artifact on Android, extract the MP4, and play it. This is the next verification milestone; a successful workflow run is not yet confirmed.
