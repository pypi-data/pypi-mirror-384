"""Endpoints related to users."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import User

UserInput = Union[User, Mapping[str, Any]]


def _serialize_users(users: Iterable[UserInput]) -> List[dict]:
    return [
        user.dict(exclude_none=True)
        if isinstance(user, User)
        else User.model_validate(user).dict(exclude_none=True)
        for user in users
    ]


async def get_users(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/v3/users")


async def get_user(client: BaseWazzupClient, user_id: str) -> Any:
    return await client._request("GET", f"/v3/users/{user_id}")


async def post_users(client: BaseWazzupClient, users: Iterable[UserInput]) -> Any:
    payload = _serialize_users(users)
    return await client._request("POST", "/v3/users", json=payload)


async def delete_user(client: BaseWazzupClient, user_id: str) -> Any:
    return await client._request("DELETE", f"/v3/users/{user_id}")


async def bulk_delete_users(client: BaseWazzupClient, user_ids: Iterable[str]) -> Any:
    ids = list(user_ids)
    return await client._request("PATCH", "/v3/users/bulk_delete", json=ids)
