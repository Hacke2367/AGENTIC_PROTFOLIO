"""Private recruiter feedback (spec 02 /feedback): one JSON record per message in an Upstash list.

The owner reads it in the Upstash console (LRANGE feedback 0 -1); it is never shown on the
site. Each visitor gets a small daily limit, keyed by the hashed visitor ID (no raw IPs).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Literal

from app import limits

KEY = "feedback"
KEEP = 1000  # newest records kept, so spam can't fill the store
MAX_MESSAGE = 500
MAX_FIELD = 80


def _daily_limit() -> int:
    return int(os.getenv("FEEDBACK_DAILY_LIMIT", "3"))


def save(visitor: str, message: str, name: str = "", company: str = "",
         now: datetime | None = None) -> Literal["saved", "limited"]:
    """Store one message unless this visitor is over today's limit. Raises LimitStoreError."""
    now = now or datetime.now(timezone.utc)
    rl_key = f"fbrl:{visitor}:{now:%Y-%m-%d}"
    _, count = limits._kv(["SET", rl_key, "0", "EX", "86400", "NX"], ["INCR", rl_key])
    if int(count) > _daily_limit():
        return "limited"
    record = json.dumps({"at": now.isoformat(timespec="seconds"), "name": name,
                         "company": company, "message": message}, ensure_ascii=False)
    limits._kv(["LPUSH", KEY, record], ["LTRIM", KEY, "0", str(KEEP - 1)])
    return "saved"
