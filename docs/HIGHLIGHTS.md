# Highlight suggestions

The `backend/app/highlights.py` module uses FFmpeg scene-change detection to propose reviewable, minimally overlapping 9:16 clip windows. This is a deterministic heuristic, **not** speech understanding or generative AI. No claims about virality or revenue are implied.

The local FastAPI starter integrates it at `GET /projects/{project_id}/highlights?asset_id=...&clip_length=30&limit=6`. This endpoint requires an authenticated owner and an uploaded asset. Scene analysis is synchronous in this checkpoint; move to the job queue before production.

Next: transcription, language-aware segment scoring, tracking, dynamic subject reframing, caption styling, and batch render controls.
