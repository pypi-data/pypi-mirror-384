"""Endpoints related to accounts management."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import AccountCreate

AccountInput = Union[AccountCreate, Mapping[str, object]]


def _serialize_account(data: AccountInput) -> dict:
    if isinstance(data, AccountCreate):
        return data.dict()
    return AccountCreate.model_validate(data).dict()


async def create_account(client: BaseWazzupClient, data: AccountInput) -> Any:
    payload = _serialize_account(data)
    return await client._request("POST", "/accounts", json=payload)


async def delete_account(client: BaseWazzupClient, account_id: int) -> Any:
    return await client._request("DELETE", f"/accounts/{account_id}")


async def get_waba_summary(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/accounts/waba-summary")


async def list_all_transactions(client: BaseWazzupClient, date: str) -> Any:
    return await client._request("GET", "/accounts/transactions", params={"date": date})
