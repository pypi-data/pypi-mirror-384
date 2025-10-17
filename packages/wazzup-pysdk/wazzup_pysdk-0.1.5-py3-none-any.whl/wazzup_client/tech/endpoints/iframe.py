"""Endpoints related to iframe generation."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import IFrameRequest, GenerateTemplatesLinkRequest

IFrameInput = Union[IFrameRequest, Mapping[str, object]]
TemplatesLinkInput = Union[GenerateTemplatesLinkRequest, Mapping[str, object]]


def _serialize_iframe(data: IFrameInput) -> dict:
    if isinstance(data, IFrameRequest):
        return data.model_dump(exclude_none=True, mode="json")
    payload = IFrameRequest.model_validate(data)
    return payload.model_dump(exclude_none=True, mode="json")


def _serialize_templates_link(data: TemplatesLinkInput) -> dict:
    if isinstance(data, GenerateTemplatesLinkRequest):
        return data.model_dump(exclude_none=True, mode="json")
    payload = GenerateTemplatesLinkRequest.model_validate(data)
    return payload.model_dump(exclude_none=True, mode="json")


async def generate_templates_link(client: BaseWazzupClient, data: TemplatesLinkInput) -> Any:
    payload = _serialize_templates_link(data)
    return await client._request("POST", "/iframe/generate-templates-link", json=payload)


async def generate_waba_profile_link(client: BaseWazzupClient, channel_id: str) -> Any:
    payload = {"channelId": channel_id}
    return await client._request("POST", "/iframe/generate-waba-profile-link", json=payload)


async def generate_chats_link(client: BaseWazzupClient, data: dict) -> Any:
    return await client._request("POST", "/iframe/generate-chats-link", json=data)


async def generate_unanswered_link(client: BaseWazzupClient, data: dict) -> Any:
    return await client._request("POST", "/iframe/generate-unanswered-link", json=data)
