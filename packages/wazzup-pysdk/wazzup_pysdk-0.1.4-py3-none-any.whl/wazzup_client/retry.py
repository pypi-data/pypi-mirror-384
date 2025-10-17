"""Retry helpers implementing decorrelated jitter backoff."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Iterable, Optional, Set

import httpx

from .exceptions import WazzupAPIError

__all__ = ("RetryOptions", "should_retry_response", "compute_backoff")


@dataclass(slots=True)
class RetryOptions:
    """Configuration controlling retry behaviour."""

    max_attempts: int = 4
    base: float = 0.5
    cap: float = 8.0
    jitter: float = 0.5
    retryable_statuses: Set[int] = field(
        default_factory=lambda: {429, 408, 502, 503, 504}
    )
    retryable_categories: Set[str] = field(
        default_factory=lambda: {"rate_limit", "server"}
    )

    def attempts_range(self) -> range:
        return range(self.max_attempts)


def should_retry_response(
    response: Optional[httpx.Response],
    error: Optional[BaseException],
    options: RetryOptions,
) -> bool:
    """Return True if the request should be retried."""
    if isinstance(error, (httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout)):
        return True
    if response is None:
        return False
    if response.status_code in options.retryable_statuses:
        return True

    if response.status_code >= 400:
        api_error = WazzupAPIError.from_response(response)
        return api_error.category in options.retryable_categories
    return False


def compute_backoff(
    attempt: int,
    *,
    base: float,
    cap: float,
    jitter: float,
) -> float:
    """Decorrelated jitter backoff implementation."""
    sleep = min(cap, base * (2 ** attempt))
    jitter_value = random.uniform(0, jitter) if jitter > 0 else 0.0
    return sleep + jitter_value
