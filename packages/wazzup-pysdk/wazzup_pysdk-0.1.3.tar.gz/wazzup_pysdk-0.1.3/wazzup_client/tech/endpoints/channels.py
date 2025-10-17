"""Endpoints related to channel management."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Union

from ...base_client import BaseWazzupClient
from ..schemas import ChannelCreate, IFrameRequest

ChannelInput = Union[ChannelCreate, Mapping[str, object]]
IFrameInput = Union[IFrameRequest, Mapping[str, object]]


def _serialize_channel(data: Optional[ChannelInput]) -> Optional[dict]:
    if data is None:
        return None
    if isinstance(data, ChannelCreate):
        return data.model_dump(exclude_none=True, mode="json")
    payload = ChannelCreate.model_validate(data)
    return payload.model_dump(exclude_none=True, mode="json")


def _serialize_iframe(data: IFrameInput) -> dict:
    if isinstance(data, IFrameRequest):
        return data.model_dump(exclude_none=True, mode="json")
    payload = IFrameRequest.model_validate(data)
    return payload.model_dump(exclude_none=True, mode="json")


async def generate_iframe_link(client: BaseWazzupClient, data: IFrameInput) -> Any:
    payload = _serialize_iframe(data)
    return await client._request("POST", "/iframe/generate-channels-link", json=payload)


async def create_channel(
    client: BaseWazzupClient, transport: str, data: Optional[ChannelInput] = None
) -> Any:
    payload = _serialize_channel(data)
    return await client._request("POST", f"/channels/{transport}", json=payload)


async def reinit_channel(client: BaseWazzupClient, transport: str, channel_id: str) -> Any:
    return await client._request("POST", f"/channels/{transport}/{channel_id}/reinit")


async def delete_channel(
    client: BaseWazzupClient, transport: str, channel_id: str, delete_chats: bool = True
) -> Any:
    payload = {"deleteChats": delete_chats}
    return await client._request("DELETE", f"/channels/{transport}/{channel_id}", json=payload)


async def list_channels(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/channels/list")


async def get_channel_info(client: BaseWazzupClient, transport: str, channel_id: str) -> Any:
    return await client._request("GET", f"/channels/{transport}/{channel_id}")
