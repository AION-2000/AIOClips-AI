# Daily football Shorts — implementation checkpoint 1

Target: **one original football Short per day**, with **explicit human approval before publishing**.

## Safety invariant
No upload worker may call YouTube unless `require_publishable(short)` succeeds on the persisted current revision. This domain policy is not a substitute for database transactions, authenticated endpoints or the final publisher integration. Any edit revokes approval. Approval is only possible after rights, factual, originality and render checks pass. Do not mark these flags true without evidence and an authorized reviewer.

## Next integration tasks
1. Persist shorts, immutable approval audit events, source evidence and render versions in PostgreSQL.
2. Enforce owner-only approval in FastAPI; never trust a caller-supplied reviewer identity.
3. Schedule one idempotent generation job per local calendar day (Asia/Dhaka).
4. Build original football-statistics-to-script-to-animated-video pipeline; do not import match broadcast footage without commercial-use authorization.
5. Build preview and approve/reject/revise UI.
6. Connect YouTube OAuth securely; publisher re-reads current persisted revision and approval in a transaction, with upload idempotency.
7. Add end-to-end tests for failed checks, stale approvals, retries, duplicate uploads and approval bypasses.

## Test
From `backend/`: `python -m unittest discover -s tests -p 'test_approval.py'`

This checkpoint implements only the approval domain policy and unit tests. It does not yet automatically create or upload videos.
