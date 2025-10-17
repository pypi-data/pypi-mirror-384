"""Mock-based smoke tests for the public and tech client methods."""

from __future__ import annotations

from dataclasses import dataclass, field
import inspect
from typing import Any, Callable, Optional, Tuple
from unittest.mock import AsyncMock, patch

import pytest

try:  # pragma: no cover - defensive shim for pydantic v2 behaviour
    import pydantic
except ImportError:  # pragma: no cover
    pydantic = None  # type: ignore[assignment]
else:
    if pydantic is not None:
        try:
            _signature = inspect.signature(pydantic.constr)
        except (TypeError, ValueError):  # pragma: no cover
            _signature = None

        if _signature is not None and "regex" not in _signature.parameters:
            _original_constr = pydantic.constr

            def _compatible_constr(*args: Any, **kwargs: Any) -> Any:
                if "regex" in kwargs:
                    kwargs["pattern"] = kwargs.pop("regex")
                return _original_constr(*args, **kwargs)

            pydantic.constr = _compatible_constr  # type: ignore[assignment]

from wazzup_client.public.client import WazzupPublicClient
from wazzup_client.tech.client import WazzupTechClient


ArgsFactory = Callable[[Any], Tuple[Any, ...]]


@dataclass(frozen=True)
class MethodCase:
    method: str
    target: str
    call_args: Tuple[Any, ...] = field(default_factory=tuple)
    call_kwargs: dict[str, Any] = field(default_factory=dict)
    expected_args_factory: Optional[ArgsFactory] = None
    expected_kwargs: Optional[dict[str, Any]] = None

    def expected_args(self, client: Any) -> Tuple[Any, ...]:
        if self.expected_args_factory is not None:
            return self.expected_args_factory(client)
        return (client, *self.call_args)

    def resolved_kwargs(self) -> dict[str, Any]:
        if self.expected_kwargs is not None:
            return self.expected_kwargs
        return self.call_kwargs


PUBLIC_METHOD_CASES = [
    MethodCase("get_users", "wazzup_client.public.endpoints.users.get_users"),
    MethodCase(
        "get_user",
        "wazzup_client.public.endpoints.users.get_user",
        call_args=("user-id",),
    ),
    MethodCase(
        "post_users",
        "wazzup_client.public.endpoints.users.post_users",
        call_args=([{"id": "u1"}],),
    ),
    MethodCase(
        "delete_user",
        "wazzup_client.public.endpoints.users.delete_user",
        call_args=("user-id",),
    ),
    MethodCase(
        "bulk_delete_users",
        "wazzup_client.public.endpoints.users.bulk_delete_users",
        call_args=(["u1", "u2"],),
    ),
    MethodCase(
        "create_contact",
        "wazzup_client.public.endpoints.contacts.create_contacts",
        call_args=({"id": "c1"},),
        expected_args_factory=lambda client: (client, [{"id": "c1"}]),
    ),
    MethodCase(
        "create_contacts",
        "wazzup_client.public.endpoints.contacts.create_contacts",
        call_args=([{"id": "c1"}, {"id": "c2"}],),
    ),
    MethodCase(
        "get_contacts",
        "wazzup_client.public.endpoints.contacts.get_contacts",
        expected_args_factory=lambda client: (client, 0),
    ),
    MethodCase(
        "get_contact",
        "wazzup_client.public.endpoints.contacts.get_contact",
        call_args=("contact-id",),
    ),
    MethodCase(
        "delete_contact",
        "wazzup_client.public.endpoints.contacts.delete_contact",
        call_args=("contact-id",),
    ),
    MethodCase(
        "bulk_delete_contacts",
        "wazzup_client.public.endpoints.contacts.bulk_delete_contacts",
        call_args=(["c1", "c2"],),
    ),
    MethodCase(
        "post_deals",
        "wazzup_client.public.endpoints.deals.create_or_update_deals",
        call_args=([{"id": "d1"}],),
    ),
    MethodCase(
        "get_deals",
        "wazzup_client.public.endpoints.deals.get_deals",
        expected_args_factory=lambda client: (client, 0),
    ),
    MethodCase(
        "get_deal",
        "wazzup_client.public.endpoints.deals.get_deal",
        call_args=("deal-id",),
    ),
    MethodCase(
        "delete_deal",
        "wazzup_client.public.endpoints.deals.delete_deal",
        call_args=("deal-id",),
    ),
    MethodCase(
        "bulk_delete_deals",
        "wazzup_client.public.endpoints.deals.bulk_delete_deals",
        call_args=(["d1", "d2"],),
    ),
    MethodCase(
        "post_pipelines",
        "wazzup_client.public.endpoints.pipelines.post_pipelines",
        call_args=([{"id": "p1"}],),
    ),
    MethodCase(
        "get_pipelines",
        "wazzup_client.public.endpoints.pipelines.get_pipelines",
    ),
    MethodCase(
        "patch_webhooks",
        "wazzup_client.public.endpoints.webhooks.patch_webhooks",
        call_args=({"url": "https://callback"},),
    ),
    MethodCase(
        "get_webhooks_settings",
        "wazzup_client.public.endpoints.webhooks.get_webhooks_settings",
    ),
    MethodCase(
        "send_message",
        "wazzup_client.public.endpoints.messages.send_message",
        call_args=({"text": "Hello"},),
    ),
    MethodCase(
        "edit_message",
        "wazzup_client.public.endpoints.messages.edit_message",
        call_args=("msg-id", {"text": "Updated"}),
    ),
    MethodCase(
        "delete_message",
        "wazzup_client.public.endpoints.messages.delete_message",
        call_args=("msg-id",),
    ),
    MethodCase(
        "get_unanswered",
        "wazzup_client.public.endpoints.counters.get_unanswered",
        call_args=("user-id",),
    ),
]


TECH_METHOD_CASES = [
    MethodCase(
        "create_account",
        "wazzup_client.tech.endpoints.accounts.create_account",
        call_args=({"name": "Example"},),
    ),
    MethodCase(
        "get_settings",
        "wazzup_client.tech.endpoints.settings.get_settings",
    ),
    MethodCase(
        "patch_settings",
        "wazzup_client.tech.endpoints.settings.patch_settings",
        call_args=({"timezone": "UTC"},),
    ),
    MethodCase(
        "generate_channel_link",
        "wazzup_client.tech.endpoints.channels.generate_iframe_link",
        call_args=({"redirect": "https://example"},),
    ),
    MethodCase(
        "create_channel",
        "wazzup_client.tech.endpoints.channels.create_channel",
        call_args=("whatsapp",),
        expected_args_factory=lambda client: (client, "whatsapp", None),
    ),
    MethodCase(
        "reinit_channel",
        "wazzup_client.tech.endpoints.channels.reinit_channel",
        call_args=("whatsapp", "channel-id"),
    ),
    MethodCase(
        "delete_channel",
        "wazzup_client.tech.endpoints.channels.delete_channel",
        call_args=("whatsapp", "channel-id"),
        expected_args_factory=lambda client: (client, "whatsapp", "channel-id", True),
    ),
    MethodCase(
        "list_channels",
        "wazzup_client.tech.endpoints.channels.list_channels",
    ),
    MethodCase(
        "generate_templates_link",
        "wazzup_client.tech.endpoints.iframe.generate_templates_link",
        call_args=({"redirect": "https://example/templates"},),
    ),
    MethodCase(
        "generate_waba_profile_link",
        "wazzup_client.tech.endpoints.iframe.generate_waba_profile_link",
        call_args=("channel-id",),
    ),
    MethodCase(
        "increase_balance",
        "wazzup_client.tech.endpoints.balance.increase_balance",
        call_args=({"amount": 100},),
    ),
    MethodCase(
        "get_balance",
        "wazzup_client.tech.endpoints.balance.get_balance",
    ),
    MethodCase(
        "get_pricing",
        "wazzup_client.tech.endpoints.waba.get_pricing",
        call_args=("US",),
    ),
    MethodCase(
        "get_transactions",
        "wazzup_client.tech.endpoints.waba.get_transactions",
        call_args=("channel-id", "2024-01-01"),
    ),
]


@pytest.mark.asyncio
@pytest.mark.parametrize("case", PUBLIC_METHOD_CASES, ids=[case.method for case in PUBLIC_METHOD_CASES])
async def test_public_client_methods(case: MethodCase) -> None:
    client = WazzupPublicClient(base_url="https://api.example.com", api_key="token")
    sentinel = object()
    try:
        with patch(case.target, new=AsyncMock(return_value=sentinel)) as mock_endpoint:
            result = await getattr(client, case.method)(*case.call_args, **case.call_kwargs)
        assert result is sentinel
        mock_endpoint.assert_awaited_once_with(*case.expected_args(client), **case.resolved_kwargs())
    finally:
        await client.close()


@pytest.mark.asyncio
@pytest.mark.parametrize("case", TECH_METHOD_CASES, ids=[case.method for case in TECH_METHOD_CASES])
async def test_tech_client_methods(case: MethodCase) -> None:
    client = WazzupTechClient(base_url="https://tech.example.com", api_key="token")
    sentinel = object()
    try:
        with patch(case.target, new=AsyncMock(return_value=sentinel)) as mock_endpoint:
            result = await getattr(client, case.method)(*case.call_args, **case.call_kwargs)
        assert result is sentinel
        mock_endpoint.assert_awaited_once_with(*case.expected_args(client), **case.resolved_kwargs())
    finally:
        await client.close()
