"""Endpoints related to webhooks."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient


async def patch_webhooks(client: BaseWazzupClient, data: Union[Mapping[str, object], dict]) -> Any:
    payload = dict(data)
    return await client._request("PATCH", "/v3/webhooks", json=payload)


async def get_webhooks_settings(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/v3/webhooks")
