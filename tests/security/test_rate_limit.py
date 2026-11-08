"""Unit tests for rate limiting."""

from __future__ import annotations

import time

from querymind.core.rate_limit import RateLimiter


def test_rate_limiter_allows_up_to_limit():
    limiter = RateLimiter(max_requests=3, window_seconds=60)
    for i in range(3):
        result = limiter.check("user-1")
        assert result.allowed is True
    assert limiter.check("user-1").allowed is False


def test_rate_limiter_keys_are_independent():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.check("user-a").allowed is True
    assert limiter.check("user-b").allowed is True  # different key
    assert limiter.check("user-a").allowed is False  # same key exhausted


def test_rate_limiter_window_expires():
    limiter = RateLimiter(max_requests=1, window_seconds=0)
    result = limiter.check("user-1")
    assert result.allowed is True
    # With window 0, timestamps expire immediately; next call allowed again.
    time.sleep(0.01)
    assert limiter.check("user-1").allowed is True


def test_rate_limiter_remaining():
    limiter = RateLimiter(max_requests=5, window_seconds=60)
    assert limiter.remaining("user-1") == 5
    limiter.check("user-1")
    assert limiter.remaining("user-1") == 4
