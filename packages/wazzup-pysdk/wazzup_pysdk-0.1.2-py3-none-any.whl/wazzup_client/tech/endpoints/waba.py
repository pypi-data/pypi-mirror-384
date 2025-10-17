"""Endpoints related to WhatsApp Business API (WABA)."""

from __future__ import annotations

from typing import Any

from ...base_client import BaseWazzupClient


async def get_pricing(client: BaseWazzupClient, country_code: str) -> Any:
    return await client._request("GET", f"/channels/waba/pricing/{country_code}")


async def get_transactions(client: BaseWazzupClient, channel_id: str, date: str) -> Any:
    return await client._request("GET", f"/channels/waba/{channel_id}/transactions/{date}")


async def list_waba_templates(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/channels/waba/templates")
