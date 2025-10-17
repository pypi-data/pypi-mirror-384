"""Endpoints related to counters."""

from __future__ import annotations

from typing import Any

from ...base_client import BaseWazzupClient


async def get_unanswered(client: BaseWazzupClient, user_id: str) -> Any:
    return await client._request("GET", f"/v3/unanswered/{user_id}")
