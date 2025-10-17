"""Endpoints related to iframe generation for the public API."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import IFrameRequest, IFrameResponse

IFrameInput = Union[IFrameRequest, Mapping[str, object]]


def _serialize_iframe(data: IFrameInput) -> dict:
    if isinstance(data, IFrameRequest):
        return data.model_dump(exclude_none=True, mode="json")
    payload = IFrameRequest.model_validate(data)
    return payload.model_dump(exclude_none=True, mode="json")


async def generate_iframe_link(client: BaseWazzupClient, data: IFrameInput) -> Any:
    """Generate iframe link for chat window.
    
    Args:
        client: Base client instance
        data: IFrame request data
        
    Returns:
        IFrame response with URL
    """
    payload = _serialize_iframe(data)
    return await client._request("POST", "/v3/iframe", json=payload)
