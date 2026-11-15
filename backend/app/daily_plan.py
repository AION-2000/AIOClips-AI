"""Pure daily scheduling decisions for one Short per Dhaka calendar day.

A scheduler may call this function repeatedly. Database-level uniqueness on
(owner_id, local_date) is still required to make concurrent workers safe.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

DHAKA = ZoneInfo("Asia/Dhaka")

@dataclass(frozen=True)
class DailyPlan:
    local_date: date
    discovery_at: datetime
    review_at: datetime
    publish_at: datetime
    key: str

def plan_day(day: date, *, owner_id: str) -> DailyPlan:
    if not owner_id or not owner_id.strip():
        raise ValueError("owner_id is required")
    if not isinstance(day, date) or isinstance(day, datetime):
        raise ValueError("Expected a calendar date")
    return DailyPlan(
        local_date=day,
        discovery_at=datetime.combine(day, time(7, 0), DHAKA),
        review_at=datetime.combine(day, time(9, 0), DHAKA),
        publish_at=datetime.combine(day, time(19, 0), DHAKA),
        key=f"{owner_id.strip()}:{day.isoformat()}",
    )

def current_plan(now: datetime, *, owner_id: str) -> DailyPlan:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("An aware timestamp is required")
    return plan_day(now.astimezone(DHAKA).date(), owner_id=owner_id)

def should_generate(plan: DailyPlan, now: datetime, *, existing_keys: set[str]) -> bool:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("An aware timestamp is required")
    return now >= plan.discovery_at and plan.key not in existing_keys

def should_publish(plan: DailyPlan, now: datetime, *, approved: bool) -> bool:
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("An aware timestamp is required")
    # Approval here is an advisory flag; the publisher MUST independently
    # re-check the persisted approval revision and rights with require_publishable.
    return approved and now >= plan.publish_at
