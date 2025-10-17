"""Endpoints related to messages."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import MessageSendRequest

MessageInput = Union[MessageSendRequest, Mapping[str, object]]


def _serialize_message(message: MessageInput) -> dict:
    if isinstance(message, MessageSendRequest):
        return message.dict(exclude_none=True)
    return MessageSendRequest.model_validate(message).dict(exclude_none=True)


async def send_message(
    client: BaseWazzupClient, msg: MessageInput
) -> Any:
    payload = _serialize_message(msg)
    return await client._request("POST", "/v3/message", json=payload, bucket_key="messages")


async def edit_message(
    client: BaseWazzupClient, message_id: str, data: Mapping[str, object]
) -> Any:
    payload = dict(data)
    return await client._request(
        "PATCH",
        f"/v3/message/{message_id}",
        json=payload,
        bucket_key="messages",
    )


async def delete_message(
    client: BaseWazzupClient, message_id: str
) -> Any:
    return await client._request("DELETE", f"/v3/message/{message_id}", bucket_key="messages")
