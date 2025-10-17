from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

import pytest

from wazzup_client.client import WazzupClient
from wazzup_client.public.schemas import ChannelItem, Contact, Deal, WebhooksSettings


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
        self._user_item = {
            "id": "u-1",
            "name": "Jane",
            "role": "manager",
        }
        self._channels = [
            {
                "channelId": "ch-1",
                "transport": "telegram",
                "plainId": "plain-1",
                "name": "Support",
                "state": "active",
            }
        ]
        self._account_settings = {
            "timezone": "UTC",
            "userRoles": [],
        }
        self._balance = {"currency": "USD", "amount": 100}

        self.list_kwargs: Dict[str, Any] = {}
        self.assign_calls: list[tuple[str, str, str, bool]] = []
        self.webhook_payload: Optional[Dict[str, Any]] = None
        self.account_create_calls: list[Dict[str, Any]] = []
        self.bulk_users_payloads: list[list[Dict[str, Any]]] = []
        self.channel_create_calls: list[tuple[str, Dict[str, Any]]] = []
        self.channel_reinit_calls: list[tuple[str, str]] = []
        self.channel_delete_calls: list[tuple[str, str, bool]] = []
        self.channel_link_payloads: list[Dict[str, Any]] = []
        self.channel_info_calls: list[tuple[str, str]] = []
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

    async def list_channels(self) -> List[Dict[str, Any]]:
        return list(self._channels)

    async def get_channel_info(self, transport: str, channel_id: str) -> Dict[str, Any]:
        self.channel_info_calls.append((transport, channel_id))
        return {"transport": transport, "channelId": channel_id}

    async def create_channel(self, transport: str, **kwargs: Any) -> Dict[str, Any]:
        payload = dict(kwargs)
        self.channel_create_calls.append((transport, payload))
        return {"channelId": "new-channel", "transport": transport} | payload

    async def reinit_channel(self, transport: str, channel_id: str) -> Dict[str, Any]:
        self.channel_reinit_calls.append((transport, channel_id))
        return {"ok": True, "channelId": channel_id}

    async def delete_channel(self, transport: str, channel_id: str, delete_chats: bool = True) -> Dict[str, Any]:
        self.channel_delete_calls.append((transport, channel_id, delete_chats))
        return {"deleted": True}

    async def generate_channel_link(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.channel_link_payloads.append(payload)
        return {"link": "https://example.com/connect", "payload": payload}

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

    # Accounts
    async def create_account(self, **data: Any) -> Dict[str, Any]:
        self.account_create_calls.append(data)
        return {"accountId": "acc-1", "apiKey": "client-key"}

    async def get_account_settings(self) -> Dict[str, Any]:
        return dict(self._account_settings)

    async def update_account_settings(self, **params: Any) -> Dict[str, Any]:
        self._account_settings.update(params)
        return dict(self._account_settings)

    async def get_balance(self) -> Dict[str, Any]:
        return dict(self._balance)

    async def get_user_channel_roles(self, user_id: str) -> List[Dict[str, Any]]:
        return [role for role in self._account_settings.get("userRoles", []) if role.get("userId") == user_id]

    # Users
    async def list_users(self) -> List[Dict[str, Any]]:
        return [dict(self._user_item)]

    async def get_user(self, user_id: str) -> Dict[str, Any]:
        return dict(self._user_item) | {"id": user_id}

    async def create_users(self, users_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.bulk_users_payloads.append(users_data)
        return {"ok": True, "users": users_data}

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
        "subscriptions": {"messagesAndStatuses": True},
    }
    assert client.webhooks.events.expected_bearer == "token"

    await client.close()


@pytest.mark.asyncio
async def test_channels_list_returns_normalized_payload(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    channels = await client.channels.list()

    assert isinstance(channels.items[0], ChannelItem)
    assert channels.raw == {"channels": stub._channels, "count": len(stub._channels)}

    await client.close()


@pytest.mark.asyncio
async def test_channels_management_helpers_delegate_to_legacy(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    await client.channels.create(transport="telegram", name="Sales")
    await client.channels.reinitialize("telegram", "ch-1")
    await client.channels.delete(transport="telegram", channel_id="ch-1", delete_chats=False)
    await client.channels.generate_link({"transport": "telegram"})

    assert stub.channel_create_calls == [("telegram", {"name": "Sales"})]
    assert stub.channel_reinit_calls == [("telegram", "ch-1")]
    assert stub.channel_delete_calls == [("telegram", "ch-1", False)]
    assert stub.channel_link_payloads == [{"transport": "telegram"}]

    await client.close()


@pytest.mark.asyncio
async def test_accounts_resource_exposes_partner_helpers(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    await client.accounts.create(name="Example")
    balance = await client.accounts.get_balance()

    assert stub.account_create_calls and stub.account_create_calls[0]["name"] == "Example"
    assert balance["amount"] == 100

    await client.close()


@pytest.mark.asyncio
async def test_users_resource_offers_raw_access(legacy_factory):
    client = WazzupClient(api_key="dummy")
    stub = legacy_factory["instance"]

    raw_users = await client.users.list_raw()
    await client.users.create_many([{"id": "u-2", "name": "John"}])

    assert raw_users == [stub._user_item]
    assert stub.bulk_users_payloads == [[{"id": "u-2", "name": "John"}]]

    await client.close()


@pytest.mark.asyncio
async def test_client_initializes_webhook_bearer_from_crm_key(legacy_factory):
    client = WazzupClient(api_key="dummy", crm_key="crm-secret")

    assert client.webhooks.events.expected_bearer == "crm-secret"

    await client.close()
