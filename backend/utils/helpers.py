"""
QueueMind — Misc Helpers
--------------------------
Utility functions used across agents and the orchestrator.
"""

import asyncio
import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import Any


# ── ID Generation ───────────────────────────────────────────────────

def make_task_id(prefix: str = "task") -> str:
    """Generate a short, unique task identifier."""
    uid = uuid.uuid4().hex[:8]
    return f"{prefix}_{uid}"


def make_worker_id(worker_type: str, index: int) -> str:
    """Generate a deterministic worker ID."""
    return f"worker_{worker_type}_{index}"


# ── Timing ──────────────────────────────────────────────────────────

def now_iso() -> str:
    """Return current UTC time as ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def elapsed_since(start: float) -> float:
    """Return seconds elapsed since a time.time() timestamp."""
    return round(time.time() - start, 3)


# ── Retry Backoff ───────────────────────────────────────────────────

def exponential_backoff(attempt: int, base: float = 2.0, max_delay: float = 60.0) -> float:
    """
    Compute exponential backoff delay with jitter.

    Args:
        attempt:   Number of previous attempts (0-indexed).
        base:      Base delay in seconds (default 2s).
        max_delay: Maximum allowed delay (default 60s).

    Returns:
        Delay in seconds.
    """
    import random
    delay = min(base ** attempt, max_delay)
    jitter = random.uniform(0, delay * 0.2)   # ±20% jitter
    return round(delay + jitter, 2)


# ── Data Helpers ─────────────────────────────────────────────────────

def sha256_hex(data: str) -> str:
    """Return first 16 chars of SHA-256 hex digest."""
    return hashlib.sha256(data.encode()).hexdigest()[:16]


def truncate(s: str, max_len: int = 80) -> str:
    """Truncate a string with ellipsis."""
    return s if len(s) <= max_len else s[:max_len - 1] + "…"


def flatten(nested: list[list[Any]]) -> list[Any]:
    """Flatten one level of nesting."""
    return [item for sublist in nested for item in sublist]


# ── Async Helpers ────────────────────────────────────────────────────

async def run_with_timeout(coro, timeout: float, fallback=None):
    """
    Run a coroutine with a timeout; return fallback if it times out.
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        return fallback


async def gather_with_concurrency(n: int, *coros):
    """
    Run coroutines with a max concurrency of n.
    Similar to asyncio.gather but throttled.
    """
    semaphore = asyncio.Semaphore(n)

    async def sem_coro(coro):
        async with semaphore:
            return await coro

    return await asyncio.gather(*(sem_coro(c) for c in coros))


# ── Summary Formatting ────────────────────────────────────────────────

def format_duration(seconds: float) -> str:
    """Human-readable duration string."""
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s}s"


def format_rate(tasks: int, elapsed_s: float) -> str:
    """Format task throughput as a string."""
    if elapsed_s <= 0:
        return "0 tasks/min"
    rate = tasks / elapsed_s * 60
    return f"{rate:.1f} tasks/min"
