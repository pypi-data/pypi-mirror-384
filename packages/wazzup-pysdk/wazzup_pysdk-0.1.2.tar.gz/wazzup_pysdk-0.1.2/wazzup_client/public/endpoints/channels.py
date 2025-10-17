"""Endpoints related to channels."""

from __future__ import annotations

from typing import Any

from ...base_client import BaseWazzupClient


async def get_channels(client: BaseWazzupClient) -> Any:
    """Get list of channels for the account.
    
    Returns:
        List of channels with their information
    """
    return await client._request("GET", "/v3/channels")
