"""Endpoints related to deals."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import Deal

DealInput = Union[Deal, Mapping[str, Any]]


def _serialize_deals(deals: Iterable[DealInput]) -> List[dict]:
    return [
        deal.dict(exclude_none=True)
        if isinstance(deal, Deal)
        else Deal.model_validate(deal).dict(exclude_none=True)
        for deal in deals
    ]


async def create_or_update_deals(
    client: BaseWazzupClient, deals: Iterable[DealInput]
) -> Any:
    payload = _serialize_deals(deals)
    return await client._request("POST", "/v3/deals", json=payload)


async def get_deals(
    client: BaseWazzupClient, offset: int = 0
) -> Any:
    return await client._request("GET", "/v3/deals", params={"offset": offset})


async def get_deal(
    client: BaseWazzupClient, deal_id: str
) -> Any:
    return await client._request("GET", f"/v3/deals/{deal_id}")


async def delete_deal(
    client: BaseWazzupClient, deal_id: str
) -> Any:
    return await client._request("DELETE", f"/v3/deals/{deal_id}")


async def bulk_delete_deals(
    client: BaseWazzupClient, deal_ids: Iterable[str]
) -> Any:
    ids = list(deal_ids)
    return await client._request("PATCH", "/v3/deals/bulk_delete", json=ids)
