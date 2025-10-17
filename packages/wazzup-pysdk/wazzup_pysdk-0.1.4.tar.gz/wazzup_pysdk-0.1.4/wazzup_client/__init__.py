"""Wazzup SDK package."""

from __future__ import annotations

from .exceptions import ErrorCategory, WazzupAPIError
from .pagination import paginate, paginate_async
from .public import WazzupPublicClient
from .rate_limiter import RateLimiter, TokenBucket
from .retry import RetryOptions
from .tech import WazzupTechClient
from .legacy_client import WazzupLegacyClient
from .client import WazzupClient, wazzup_client_context

__all__ = (
    "__version__",
    "ErrorCategory",
    "RateLimiter",
    "RetryOptions",
    "TokenBucket",
    "WazzupAPIError",
    "WazzupLegacyClient",
    "WazzupClient",
    "wazzup_client_context",
    "WazzupPublicClient",
    "WazzupTechClient",
    "paginate",
    "paginate_async",
)

__version__ = "0.1.0"
