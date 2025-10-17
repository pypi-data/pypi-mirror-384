"""Base async HTTP client for the Wazzup SDK."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from typing import Any, Mapping, Optional, Union

import httpx

from .exceptions import WazzupAPIError
from .rate_limiter import RateLimiter
from .retry import RetryOptions, compute_backoff, should_retry_response

__all__ = ("ClientTimeouts", "BaseWazzupClient")


@dataclass(slots=True)
class ClientTimeouts:
    """Collection of timeout settings used to configure httpx."""

    connect: float = 5.0
    read: float = 30.0
    write: float = 10.0
    pool: float = 5.0

    def to_httpx_timeout(self) -> httpx.Timeout:
        return httpx.Timeout(
            connect=self.connect,
            read=self.read,
            write=self.write,
            pool=self.pool,
        )


def _parse_retry_after(header_value: Optional[str]) -> Optional[float]:
    if not header_value:
        return None
    try:
        return float(header_value)
    except (TypeError, ValueError):
        try:
            dt = parsedate_to_datetime(header_value)
        except (TypeError, ValueError, OverflowError):
            return None
        if dt is None:
            return None
        return max(0.0, (dt - dt.now(dt.tzinfo)).total_seconds())


class BaseWazzupClient:
    """Shared async HTTP client with retry-aware request helper."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: Optional[Union[float, ClientTimeouts, httpx.Timeout]] = None,
        max_retries: int = 4,
        *,
        retry_options: Optional[RetryOptions] = None,
        rate_limiter: Optional[RateLimiter] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._timeouts = self._resolve_timeouts(timeout)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            timeout=self._timeouts,
        )
        self._retry_options = (retry_options or RetryOptions(max_attempts=max_retries))
        self._rate_limiter = rate_limiter or RateLimiter()
        if not self._rate_limiter.has_bucket("messages"):
            self._rate_limiter.register_bucket(
                "messages",
                self._rate_limiter.default_capacity,
                self._rate_limiter.default_refill_rate,
            )

    @staticmethod
    def _resolve_timeouts(
        timeout: Optional[Union[float, ClientTimeouts, httpx.Timeout]],
    ) -> httpx.Timeout:
        if timeout is None:
            return ClientTimeouts().to_httpx_timeout()
        if isinstance(timeout, (int, float)):
            return httpx.Timeout(timeout)
        if isinstance(timeout, ClientTimeouts):
            return timeout.to_httpx_timeout()
        return timeout

    def _bucket_key_for_endpoint(self, endpoint: str) -> str:
        lowered = endpoint.lower()
        if "/message" in lowered:
            return "messages"
        return "default"

    async def _wait_rate_limit(self, endpoint: str, *, bucket_key: Optional[str], tokens: float) -> None:
        if not self._rate_limiter:
            return
        key = bucket_key or self._bucket_key_for_endpoint(endpoint)
        await self._rate_limiter.acquire(key, tokens)

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        json: Any = None,
        retry_options: Optional[RetryOptions] = None,
        bucket_key: Optional[str] = None,
        tokens: float = 1.0,
        **kwargs: Any,
    ) -> Any:
        """Perform an HTTP request with retry, backoff, and rate limiting."""
        options = retry_options or self._retry_options
        await self._wait_rate_limit(endpoint, bucket_key=bucket_key, tokens=tokens)

        response: Optional[httpx.Response] = None
        error: Optional[BaseException] = None

        for attempt in options.attempts_range():
            try:
                response = await self._client.request(
                    method,
                    endpoint,
                    params=params,
                    json=json,
                    **kwargs,
                )
                error = None
            except BaseException as exc:  # noqa: PERF203 - we need to retry on broad httpx exceptions
                response = None
                error = exc

            if response is not None and response.status_code < 400:
                if response.status_code == 204 or not response.content:
                    return None
                return response.json()

            final_attempt = attempt >= options.max_attempts - 1

            if response is None:
                if final_attempt or not should_retry_response(None, error, options):
                    raise error  # type: ignore[misc]
                await asyncio.sleep(compute_backoff(attempt, base=options.base, cap=options.cap, jitter=options.jitter))
                continue

            api_error = WazzupAPIError.from_response(response)
            if final_attempt or not should_retry_response(response, None, options):
                raise api_error

            retry_after = _parse_retry_after(response.headers.get("Retry-After")) if response.status_code == 429 else None
            delay = retry_after or compute_backoff(attempt, base=options.base, cap=options.cap, jitter=options.jitter)
            await asyncio.sleep(delay)

        # Defensive: loop should always return or raise
        raise RuntimeError("Retry loop exhausted without returning or raising")

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
