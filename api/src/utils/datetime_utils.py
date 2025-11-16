"""Datetime utilities for Singapore timezone (SGT)"""

from datetime import datetime
import pytz

# Singapore timezone
SGT = pytz.timezone('Asia/Singapore')


def now_sgt() -> datetime:
    """Get current datetime in Singapore timezone (UTC+8)"""
    return datetime.now(SGT)


def utc_to_sgt(dt: datetime) -> datetime:
    """Convert UTC datetime to Singapore timezone"""
    if dt.tzinfo is None:
        # Assume UTC if naive
        dt = pytz.utc.localize(dt)
    return dt.astimezone(SGT)


def sgt_to_utc(dt: datetime) -> datetime:
    """Convert Singapore timezone to UTC"""
    if dt.tzinfo is None:
        # Assume SGT if naive
        dt = SGT.localize(dt)
    return dt.astimezone(pytz.utc)
