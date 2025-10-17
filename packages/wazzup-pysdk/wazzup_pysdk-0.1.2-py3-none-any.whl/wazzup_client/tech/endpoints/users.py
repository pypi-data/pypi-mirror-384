"""Endpoints related to user management."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import TechUser

UserInput = Union[TechUser, Mapping[str, object]]


def _serialize_user(data: UserInput) -> dict:
    if isinstance(data, TechUser):
        return data.dict()
    return TechUser.model_validate(data).dict()


async def create_user(client: BaseWazzupClient, data: UserInput) -> Any:
    payload = _serialize_user(data)
    return await client._request("POST", "/users", json=payload)


async def delete_user(client: BaseWazzupClient, user_id: str) -> Any:
    return await client._request("DELETE", f"/users/{user_id}")


async def list_users(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/users")
