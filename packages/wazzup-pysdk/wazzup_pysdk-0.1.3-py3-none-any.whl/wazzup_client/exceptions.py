"""Custom exceptions raised by the Wazzup SDK."""

from __future__ import annotations

from typing import Any, Dict, Literal, Optional, Set

import httpx

ErrorCategory = Literal[
    "validation",
    "transport",
    "channel",
    "limit",
    "spam",
    "window",
    "rate_limit",
    "server",
    "conflict",
    "unknown",
]

__all__ = ("ErrorCategory", "WazzupAPIError")


_VALIDATION_PREFIXES: tuple[str, ...] = ("INVALID_", "VALIDATION_ERROR", "MESSAGE_ONLY_TEXT_OR_CONTENT")
_CONFLICT_ERRORS: Set[str] = {"REPEATED_CRM_MESSAGE_ID"}
_TRANSPORT_ERRORS: Set[str] = {"WRONG_TRANSPORT", "MESSAGES_ABNORMAL_SEND", "MESSAGES_INVALID_CONTACT_TYPE"}
_CHANNEL_ERRORS: Set[str] = {
    "CHANNEL_NOT_FOUND",
    "CHANNEL_BLOCKED",
    "CHANNEL_WAPI_REJECTED",
    "MESSAGE_CHANNEL_UNAVAILABLE",
    "CHANNEL_NO_MONEY",
    "NOTENOUGHMONEY",
}
_LIMIT_ERRORS: Set[str] = {
    "MESSAGE_TEXT_TOO_LONG",
    "MESSAGES_TOO_LONG",
    "MESSAGES_TOO_LONG_TEXT",
    "MESSAGES_TOO_LONG_CAPTION",
    "MESSAGE_WRONG_CONTENT_TYPE",
    "MESSAGES_UNSUPPORTED_CONTENT_TYPE_INSTAPI",
    "MESSAGES_CONTENT_SIZE_EXCEEDED",
    "MESSAGES_CONTENT_SIZE_EXCEEDED_IMAGE",
    "MESSAGES_CONTENT_SIZE_EXCEEDED_DOCUMENT",
    "MESSAGES_CONTENT_CAN_NOT_BE_BLANK",
}
_SPAM_ERRORS: Set[str] = {"MESSAGES_IS_SPAM", "TEMPLATE_REJECTED"}
_WINDOW_ERRORS: Set[str] = {"24_HOURS_EXCEEDED", "7_DAYS_EXCEEDED"}
_SERVER_ERRORS: Set[str] = {"UNKNOWN_ERROR", "UNKNOWN_ERROR_WITH_TRACE_ID"}


class WazzupAPIError(Exception):
    """Represents an error returned by the Wazzup API."""

    status_code: int
    error: str
    description: Optional[str]
    data: Optional[Any]
    category: ErrorCategory

    def __init__(
        self,
        status_code: int,
        error: str,
        description: Optional[str] = None,
        data: Optional[Any] = None,
        *,
        category: Optional[ErrorCategory] = None,
    ) -> None:
        self.status_code = status_code
        self.error = error or "unknown_error"
        self.description = description
        self.data = data
        self.category = category or self._categorize(status_code, self.error)
        super().__init__(f"[{status_code}] {self.error} ({self.category}): {description or ''}".strip())

    @classmethod
    def from_response(cls, response: httpx.Response) -> "WazzupAPIError":
        """Build an exception from an HTTPX response object."""
        try:
            payload = response.json()
        except Exception:
            payload = {"description": response.text}
        return cls(
            response.status_code,
            str(payload.get("error", "unknown_error")),
            payload.get("description"),
            payload.get("data"),
        )

    @staticmethod
    def _categorize(status_code: int, error: str) -> ErrorCategory:
        normalized = (error or "unknown_error").upper()
        if status_code == 429 or normalized == "TOO_MANY_REQUESTS":
            return "rate_limit"
        if status_code == 409 or normalized in _CONFLICT_ERRORS:
            return "conflict"
        if status_code >= 500 or normalized in _SERVER_ERRORS:
            return "server"
        if any(normalized.startswith(prefix) for prefix in _VALIDATION_PREFIXES) or normalized in _VALIDATION_PREFIXES:
            return "validation"
        if normalized in _TRANSPORT_ERRORS:
            return "transport"
        if normalized in _CHANNEL_ERRORS:
            return "channel"
        if normalized in _LIMIT_ERRORS:
            return "limit"
        if normalized in _SPAM_ERRORS:
            return "spam"
        if normalized in _WINDOW_ERRORS:
            return "window"
        if status_code >= 400 and status_code < 500:
            return "unknown"
        return "unknown"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the error for logging or transport."""
        return {
            "status_code": self.status_code,
            "error": self.error,
            "description": self.description,
            "data": self.data,
            "category": self.category,
        }
