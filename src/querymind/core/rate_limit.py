"""Rate limiting and abuse prevention.

Sliding-window rate limiter keyed by identifier (e.g. user id, IP, or
API key). Configurable request limit and window. Production deployments
should back this with Redis for distributed deployments.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class RateLimitResult:
    allowed: bool
    remaining: int
    reset_at: float
    limit: int


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(
        self,
        *,
        max_requests: int,
        window_seconds: int,
    ) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._timestamps: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> RateLimitResult:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._timestamps[key]
        # Drop timestamps outside the window.
        timestamps[:] = [t for t in timestamps if t > window_start]

        if len(timestamps) >= self.max_requests:
            reset_at = timestamps[0] + self.window_seconds if timestamps else now + self.window_seconds
            return RateLimitResult(
                allowed=False,
                remaining=0,
                reset_at=reset_at,
                limit=self.max_requests,
            )

        timestamps.append(now)
        remaining = self.max_requests - len(timestamps)
        reset_at = now + self.window_seconds
        return RateLimitResult(
            allowed=True,
            remaining=remaining,
            reset_at=reset_at,
            limit=self.max_requests,
        )

    def remaining(self, key: str) -> int:
        now = time.time()
        window_start = now - self.window_seconds
        timestamps = self._timestamps.get(key, [])
        valid = [t for t in timestamps if t > window_start]
        return max(0, self.max_requests - len(valid))

    def clear(self, key: str) -> None:
        self._timestamps.pop(key, None)


# Default limiters keyed by setting values.
def build_rate_limiter(
    max_requests: int = 100, window_seconds: int = 60
) -> RateLimiter:
    return RateLimiter(max_requests=max_requests, window_seconds=window_seconds)
