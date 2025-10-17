"""Endpoints related to contacts."""

from __future__ import annotations

from typing import Any, Iterable, List, Mapping, Union

from ...base_client import BaseWazzupClient
from ..schemas import Contact

ContactInput = Union[Contact, Mapping[str, Any]]


def _serialize_contacts(contacts: Iterable[ContactInput]) -> List[dict]:
    return [
        contact.dict(exclude_none=True)
        if isinstance(contact, Contact)
        else Contact.model_validate(contact).dict(exclude_none=True)
        for contact in contacts
    ]


async def create_contacts(
    client: BaseWazzupClient, contacts: Iterable[ContactInput]
) -> Any:
    payload = _serialize_contacts(contacts)
    return await client._request("POST", "/v3/contacts", json=payload)


async def get_contacts(
    client: BaseWazzupClient, offset: int = 0
) -> Any:
    return await client._request("GET", "/v3/contacts", params={"offset": offset})


async def get_contact(
    client: BaseWazzupClient, contact_id: str
) -> Any:
    return await client._request("GET", f"/v3/contacts/{contact_id}")


async def delete_contact(
    client: BaseWazzupClient, contact_id: str
) -> Any:
    return await client._request("DELETE", f"/v3/contacts/{contact_id}")


async def bulk_delete_contacts(
    client: BaseWazzupClient, contact_ids: Iterable[str]
) -> Any:
    ids = list(contact_ids)
    return await client._request("PATCH", "/v3/contacts/bulk_delete", json=ids)
