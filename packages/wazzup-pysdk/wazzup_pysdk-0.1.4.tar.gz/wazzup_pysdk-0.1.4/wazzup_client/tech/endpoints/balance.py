"""Endpoints related to balance management."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import BalanceChange

BalanceInput = Union[BalanceChange, Mapping[str, object]]


def _serialize_balance(data: BalanceInput) -> dict:
    if isinstance(data, BalanceChange):
        return data.dict()
    return BalanceChange.model_validate(data).dict()


async def increase_balance(client: BaseWazzupClient, data: BalanceInput) -> Any:
    payload = _serialize_balance(data)
    return await client._request("POST", "/accounts/balance", json=payload)


async def get_balance(client: BaseWazzupClient) -> Any:
    return await client._request("GET", "/accounts/balance")
