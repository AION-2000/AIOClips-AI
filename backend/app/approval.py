"""Publishing approval policy. Pure domain logic; no API side effects."""
from __future__ import annotations
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum

class Status(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    PUBLISHED = "published"

@dataclass(frozen=True)
class Short:
    id: str
    status: Status = Status.DRAFT
    rights_verified: bool = False
    facts_verified: bool = False
    original_content_verified: bool = False
    render_ready: bool = False
    approved_by: str | None = None
    approved_at: datetime | None = None
    revision: int = 1
    approved_revision: int | None = None

class ApprovalError(ValueError):
    pass

def submit_for_review(short: Short) -> Short:
    if short.status not in (Status.DRAFT, Status.REJECTED):
        raise ApprovalError("Only drafts or rejected videos may enter review")
    return replace(short, status=Status.REVIEW, approved_by=None,
                   approved_at=None, approved_revision=None)

def approve(short: Short, *, reviewer: str, now: datetime | None = None) -> Short:
    if short.status != Status.REVIEW:
        raise ApprovalError("Video must be awaiting review")
    if not reviewer.strip():
        raise ApprovalError("An authenticated human reviewer is required")
    if not all((short.rights_verified, short.facts_verified,
                short.original_content_verified, short.render_ready)):
        raise ApprovalError("All rights, factual, originality and render checks must pass")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ApprovalError("Approval timestamp must be timezone aware")
    return replace(short, status=Status.APPROVED, approved_by=reviewer.strip(),
                   approved_at=now, approved_revision=short.revision)

def reject(short: Short) -> Short:
    if short.status != Status.REVIEW:
        raise ApprovalError("Only videos awaiting review can be rejected")
    return replace(short, status=Status.REJECTED)

def revise(short: Short) -> Short:
    if short.status == Status.PUBLISHED:
        raise ApprovalError("Published videos cannot be revised in place")
    return replace(short, revision=short.revision + 1, status=Status.DRAFT,
                   approved_by=None, approved_at=None, approved_revision=None,
                   facts_verified=False, original_content_verified=False,
                   render_ready=False)

def require_publishable(short: Short) -> None:
    if (short.status != Status.APPROVED or not short.approved_by
            or short.approved_at is None or short.approved_revision != short.revision
            or not all((short.rights_verified, short.facts_verified,
                        short.original_content_verified, short.render_ready))):
        raise ApprovalError("Publication blocked: explicit approval of current verified revision required")

def mark_published(short: Short) -> Short:
    require_publishable(short)
    return replace(short, status=Status.PUBLISHED)
