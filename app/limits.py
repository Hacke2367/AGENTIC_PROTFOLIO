"""Usage caps: ~20 messages per visitor per hour, and a site-wide daily OpenAI spend cap.

Counters live in Upstash Redis (REST) so they survive serverless instance recycling
(plan D6, via httpx2 which openai already installs). Without KV env vars they fall back to process memory, which is fine for local dev only.
Any store error is treated as "daily cap reached" by the caller (plan D7: fail closed).
"""
from __future__ import annotations

import hashlib
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

import httpx2


@dataclass(frozen=True)
class LimitDecision:
    allowed: bool
    reason: Literal["ok", "visitor", "daily"]


class LimitStoreError(Exception):
    """The counter store could not be read or written."""


def _visitor_limit() -> int:
    return int(os.getenv("VISITOR_HOURLY_LIMIT", "20"))


def _daily_budget_micro() -> int:
    return int(float(os.getenv("DAILY_BUDGET_USD", "1.0")) * 1_000_000)


# --- store: Upstash REST pipeline, or process memory --------------------------------------

_memory: dict[str, tuple[object, float]] = {}  # key -> (value, expires_at); lists for LPUSH


def reset_memory() -> None:
    _memory.clear()


def _memory_run(cmd: list[str]):
    # chisle: implements only the commands this module sends; per-process, never for prod
    now = time.time()
    op, key = cmd[0], cmd[1]
    value, exp = _memory.get(key, (None, 0.0))
    if value is not None and exp and exp <= now:
        value = None
    if op == "GET":
        return value
    if op == "SET":  # SET key val EX sec NX
        if value is None:
            _memory[key] = (int(cmd[2]), now + int(cmd[4]))
        return None
    if op in ("INCR", "INCRBY"):
        new = (value or 0) + (int(cmd[2]) if op == "INCRBY" else 1)
        _memory[key] = (new, exp if value is not None else 0.0)
        return new
    if op == "EXPIRE":
        if value is not None:
            _memory[key] = (value, now + int(cmd[2]))
        return 1
    if op == "LPUSH":  # feedback list (plan 02 D9)
        items = [cmd[2], *(value or [])]
        _memory[key] = (items, exp if value is not None else 0.0)
        return len(items)
    if op == "LTRIM":  # LTRIM key start stop (inclusive)
        if value is not None:
            _memory[key] = (value[int(cmd[2]):int(cmd[3]) + 1], exp)
        return "OK"
    raise ValueError(op)


def _kv(*commands: list[str]) -> list:
    url, token = os.getenv("KV_REST_API_URL"), os.getenv("KV_REST_API_TOKEN")
    if not (url and token):
        return [_memory_run(c) for c in commands]
    try:
        resp = httpx2.post(f"{url.rstrip('/')}/pipeline", json=list(commands),
                          headers={"Authorization": f"Bearer {token}"}, timeout=3)
        resp.raise_for_status()
        results = resp.json()
    except (httpx2.HTTPError, ValueError) as exc:
        raise LimitStoreError(str(exc)) from exc
    if any("error" in r for r in results):
        raise LimitStoreError(str(results))
    return [r.get("result") for r in results]


# --- public API ---------------------------------------------------------------------------

def visitor_id(request) -> str:
    """Hashed client IP: raw IPs are never stored (plan D12)."""
    forwarded = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
    ip = forwarded or (request.client.host if request.client else "unknown")
    secret = os.getenv("STATE_SECRET", "")
    return hashlib.sha256(f"{ip}|{secret}".encode()).hexdigest()[:16]


def check(visitor: str, now: datetime | None = None) -> LimitDecision:
    now = now or datetime.now(timezone.utc)
    spend_key = f"spend:{now:%Y-%m-%d}"
    rl_key = f"rl:{visitor}:{now:%Y%m%d%H}"
    # One round trip. The visitor counter also ticks when the daily cap is closed; harmless,
    # since nobody can chat then anyway.
    spend, _, count = _kv(["GET", spend_key],
                          ["SET", rl_key, "0", "EX", "3600", "NX"],
                          ["INCR", rl_key])
    if int(spend or 0) >= _daily_budget_micro():
        return LimitDecision(False, "daily")
    if int(count) > _visitor_limit():
        return LimitDecision(False, "visitor")
    return LimitDecision(True, "ok")


def record_spend(usd: float, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    key = f"spend:{now:%Y-%m-%d}"
    _kv(["INCRBY", key, str(max(round(usd * 1_000_000), 1))], ["EXPIRE", key, "172800"])
