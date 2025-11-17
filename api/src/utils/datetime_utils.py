"""Datetime utilities for Singapore timezone (SGT)"""

from datetime import datetime, timezone, timedelta

# Singapore timezone is UTC+8
SGT = timezone(timedelta(hours=8))


def now_sgt() -> datetime:
    """Get current datetime in Singapore timezone (UTC+8) as naive datetime"""
    return datetime.now(SGT).replace(tzinfo=None)


def utc_to_sgt(dt: datetime) -> datetime:
    """Convert UTC datetime to Singapore timezone"""
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(SGT)


def sgt_to_utc(dt: datetime) -> datetime:
    """Convert Singapore timezone to UTC"""
    if dt.tzinfo is None:
        # Assume SGT if naive
        dt = dt.replace(tzinfo=SGT)
    return dt.astimezone(timezone.utc)
