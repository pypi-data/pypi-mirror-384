"""Async token bucket rate limiter used by the Wazzup SDK."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from time import monotonic
from typing import Dict, Optional

__all__ = ("RateLimiter", "TokenBucket")


@dataclass(slots=True)
class TokenBucket:
    """Simple asyncio-friendly token bucket."""

    capacity: float
    refill_rate: float  # tokens per second
    tokens: float = field(init=False)
    _last_refill: float = field(init=False, repr=False)
    _lock: asyncio.Lock = field(init=False, repr=False, default_factory=asyncio.Lock)

    def __post_init__(self) -> None:
        self.tokens = self.capacity
        self._last_refill = monotonic()

    def _refill(self) -> None:
        now = monotonic()
        elapsed = max(0.0, now - self._last_refill)
        self._last_refill = now
        if elapsed and self.refill_rate > 0:
            self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)

    async def acquire(self, tokens: float = 1.0) -> None:
        """Wait until the bucket has the requested amount of tokens."""
        while True:
            async with self._lock:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                if self.refill_rate <= 0:
                    wait_time = 0.1
                else:
                    missing = tokens - self.tokens
                    wait_time = max(0.05, missing / self.refill_rate)
            await asyncio.sleep(wait_time)


class RateLimiter:
    """A collection of token buckets identified by keys."""

    def __init__(
        self,
        default_capacity: float = 500.0,
        default_refill_rate: float = 100.0,
        buckets: Optional[Dict[str, TokenBucket]] = None,
    ) -> None:
        self._default_capacity = default_capacity
        self._default_refill_rate = default_refill_rate
        self._buckets: Dict[str, TokenBucket] = buckets or {}
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default", tokens: float = 1.0) -> None:
        bucket = await self._get_or_create_bucket(key)
        await bucket.acquire(tokens)

    async def _get_or_create_bucket(self, key: str) -> TokenBucket:
        try:
            return self._buckets[key]
        except KeyError:
            async with self._lock:
                bucket = self._buckets.get(key)
                if bucket is None:
                    bucket = TokenBucket(self._default_capacity, self._default_refill_rate)
                    self._buckets[key] = bucket
                return bucket

    def register_bucket(self, key: str, capacity: float, refill_rate: float) -> None:
        """Register or overwrite a token bucket for a route."""
        self._buckets[key] = TokenBucket(capacity, refill_rate)

    def has_bucket(self, key: str) -> bool:
        return key in self._buckets

    @property
    def default_capacity(self) -> float:
        return self._default_capacity

    @property
    def default_refill_rate(self) -> float:
        return self._default_refill_rate
