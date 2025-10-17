"""Utility helpers for offset-based pagination."""

from __future__ import annotations

from collections.abc import AsyncIterator, Awaitable, Callable, Iterable, Iterator
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class SupportsData(Protocol):
    data: Iterable[T]


def _extract_items(page: Any) -> Iterable[T]:
    if page is None:
        return ()
    if isinstance(page, dict) and "data" in page:
        data = page.get("data") or ()
        if isinstance(data, Iterable):
            return data
        return ()
    if isinstance(page, Iterable) and not isinstance(page, (str, bytes)):
        return page
    if hasattr(page, "data"):
        return getattr(page, "data")
    return ()


def paginate(fetch_page: Callable[[int], Any], *, page_size: int = 100) -> Iterator[T]:
    """Iterate through an entire offset-based collection."""
    offset = 0
    while True:
        page = fetch_page(offset)
        items = list(_extract_items(page))
        if not items:
            break
        for item in items:
            yield item
        if len(items) < page_size:
            break
        offset += len(items)


async def paginate_async(
    fetch_page: Callable[[int], Awaitable[Any]],
    *,
    page_size: int = 100,
) -> AsyncIterator[T]:
    """Async variant of :func:`paginate`."""
    offset = 0
    while True:
        page = await fetch_page(offset)
        items = list(_extract_items(page))
        if not items:
            break
        for item in items:
            yield item
        if len(items) < page_size:
            break
        offset += len(items)
