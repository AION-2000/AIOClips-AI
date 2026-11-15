# Channel launch checklist — AIOClips AI

## Creator accounts
- Create YouTube and any other platform accounts yourself, using strong unique passwords and MFA.
- Use consistent channel name, handle, avatar and description across platforms.
- Do not share passwords, recovery codes or OAuth refresh tokens in chat or GitHub.
- Review platform eligibility, monetization and AI/synthetic-media disclosure requirements before uploading.
- Use original narration and visuals or keep evidence of commercial rights for each imported asset.
- Record the account/channel IDs later in environment variables, never as hardcoded secrets.

## Daily pipeline contract
- One candidate per local day (Asia/Dhaka), generated at 07:00, review ready target 09:00.
- Proposed publication time 19:00 only after human approval of that exact revision.
- If not approved, skip publication; never auto-approve.
- Persist one daily record per owner/date with a database unique constraint and job idempotency key.
- Any video edit invalidates prior approval.
- API uploads require OAuth authorization and may be subject to platform API verification or upload restrictions.

## Implementation state
`app.daily_plan` is a pure scheduling policy and does not itself run a worker.
`app.approval` is a pure approval policy and does not itself protect an HTTP endpoint.
The scheduler, persistence, approval UI, publisher and video generator are upcoming integration work.
