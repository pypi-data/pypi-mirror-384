from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import pytest

from wazzup_client.client import WazzupClient
from wazzup_client.public.schemas import Contact, Deal, WebhooksSettings


class LegacyStub:
    def __init__(self) -> None:
        contact_item = {
            "id": "c-1",
            "responsibleUserId": "u-1",
            "name": "Alice",
            "contactData": [
                {"chatType": "telegram", "chatId": "tg-1"}
            ],
        }
        deal_item = {
            "id": "d-1",
            "responsibleUserId": "u-1",
            "name": "Test deal",
            "contacts": ["c-1"],
            "uri": "https://example.com/deals/1",
        }

        self._contact_item = contact_item
        self._deal_item = deal_item

        self.list_kwargs: Dict[str, Any] = {}
        self.assign_calls: list[tuple[str, str, str, bool]] = []
        self.webhook_payload: Optional[Dict[str, Any]] = None
        self.closed = False

    # Contacts
    async def list_contacts(self, **params: Any) -> Dict[str, Any]:
        self.list_kwargs = params
        return {"data": [self._contact_item]}

    async def get_contact(self, contact_id: str) -> Dict[str, Any]:
        return self._contact_item | {"id": contact_id}

    async def create_contact(self, **data: Any) -> Dict[str, Any]:
        return data

    # Deals
    async def create_deal(self, **data: Any) -> Dict[str, Any]:
        return self._deal_item | data

    # Channels
    async def assign_user_to_channel(
        self,
        *,
        user_id: str,
        channel_id: str,
        role: str,
        allow_get_new_clients: bool,
    ) -> Dict[str, Any]:
        self.assign_calls.append((user_id, channel_id, role, allow_get_new_clients))
        return {"ok": True}

    # Webhooks
    async def get_webhook_settings(self) -> Dict[str, Any]:
        return {
            "webhooksUri": "https://example.com/webhooks",
            "webhooksAuthToken": "secret",
        }

    async def update_webhook_settings(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        self.webhook_payload = settings
        return settings

    async def test_webhook(self, uri: str) -> Dict[str, Any]:
        return {"success": True, "uri": uri}

    async def close(self) -> None:
        self.closed = True


@pytest.fixture
def legacy_factory(monkeypatch):
    holder: Dict[str, LegacyStub] = {}

    def factory(*_args: Any, **_kwargs: Any) -> LegacyStub:
        stub = LegacyStub()
        holder["instance"] = stub
        return stub

    monkeypatch.setattr("wazzup_client.client.WazzupLegacyClient", factory)
    return holder


@pytest.mark.asyncio
async def test_contacts_list_returns_typed_resource(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    resource_list = await client.contacts.list(offset=5)

    assert isinstance(resource_list.items[0], Contact)
    assert stub.list_kwargs == {"offset": 5}

    await client.close()
    assert stub.closed


@pytest.mark.asyncio
async def test_contacts_get_returns_model(legacy_factory):
    client = WazzupClient(api_key="dummy")

    contact = await client.contacts.get("c-42")

    assert isinstance(contact, Contact)
    assert contact.id == "c-42"

    await client.close()


@pytest.mark.asyncio
async def test_deals_update_falls_back_to_create(legacy_factory):
    client = WazzupClient(api_key="dummy")

    updated = await client.deals.update("d-1", name="Renamed")

    assert isinstance(updated, dict | Deal)  # type: ignore[arg-type]
    if isinstance(updated, dict):
        assert updated["name"] == "Renamed"
    else:
        assert isinstance(updated, Deal)
        assert updated.name == "Renamed"

    await client.close()


@pytest.mark.asyncio
async def test_channels_assign_user_delegates_to_legacy(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    await client.channels.assign_user("u-55", "ch-99", role="manager", allow_get_new_clients=False)

    assert stub.assign_calls == [("u-55", "ch-99", "manager", False)]

    await client.close()


@pytest.mark.asyncio
async def test_webhooks_namespace_ensure_updates_settings(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    settings = await client.webhooks.ensure(
        uri="https://listener",
        auth_token="token",
        subscriptions={"messagesAndStatuses": True},
    )

    assert isinstance(settings, WebhooksSettings)
    assert stub.webhook_payload == {
        "webhooksUri": "https://listener",
        "webhooksAuthToken": "token",
        "subscriptions": {"messagesAndStatuses": True},
    }
    assert client.webhooks.events.expected_bearer == "token"

    await client.close()


@pytest.mark.asyncio
async def test_client_initializes_webhook_bearer_from_crm_key(legacy_factory):
    client = WazzupClient(api_key="dummy", crm_key="crm-secret")

    assert client.webhooks.events.expected_bearer == "crm-secret"

    await client.close()
