"""Endpoints related to settings management."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import SettingsPatch

SettingsInput = Union[SettingsPatch, Mapping[str, object]]


def _serialize_settings(data: SettingsInput) -> dict:
    if isinstance(data, SettingsPatch):
        return data.dict(exclude_none=True)
    return SettingsPatch.model_validate(data).dict(exclude_none=True)


async def get_settings(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/settings")


async def patch_settings(client: BaseWazzupClient, data: SettingsInput) -> Any:
    payload = _serialize_settings(data)
    return await client._request("PATCH", "/settings", json=payload)
