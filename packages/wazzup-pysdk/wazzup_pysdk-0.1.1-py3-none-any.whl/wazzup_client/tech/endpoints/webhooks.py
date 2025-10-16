"""Endpoints related to webhook management."""

from __future__ import annotations

from typing import Any

from ...base_client import BaseWazzupClient


async def send_test_webhook(client: BaseWazzupClient, uri: str) -> Any:
    payload = {"webhooksUri": uri}
    return await client._request("POST", "/webhooks/test", json=payload)
