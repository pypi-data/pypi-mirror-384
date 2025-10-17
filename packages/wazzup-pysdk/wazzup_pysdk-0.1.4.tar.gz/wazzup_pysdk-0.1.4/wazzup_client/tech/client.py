"""Async client for the tech partner Wazzup API."""

from __future__ import annotations

from typing import Any, Mapping, Union

from ..base_client import BaseWazzupClient
from .endpoints import accounts, balance, channels, iframe, settings, users, waba, webhooks
from .schemas import AccountCreate, BalanceChange, ChannelCreate, GenerateTemplatesLinkRequest, IFrameRequest, SettingsPatch, TechUser

MappingLike = Mapping[str, Any]

AccountInput = Union[AccountCreate, MappingLike]
SettingsInput = Union[SettingsPatch, MappingLike]
ChannelInput = Union[ChannelCreate, MappingLike, None]
IFrameInput = Union[IFrameRequest, MappingLike]
TemplatesLinkInput = Union[GenerateTemplatesLinkRequest, MappingLike]
BalanceInput = Union[BalanceChange, MappingLike]
UserInput = Union[TechUser, MappingLike]


class WazzupTechClient(BaseWazzupClient):
    """Client for https://tech.wazzup24.com/"""

    async def create_account(self, data: AccountInput) -> Any:
        return await accounts.create_account(self, data)

    async def get_settings(self) -> Any:
        return await settings.get_settings(self)

    async def patch_settings(self, data: SettingsInput) -> Any:
        return await settings.patch_settings(self, data)

    async def generate_channel_link(self, data: IFrameInput) -> Any:
        return await channels.generate_iframe_link(self, data)

    async def create_channel(self, transport: str, data: ChannelInput = None) -> Any:
        return await channels.create_channel(self, transport, data)

    async def reinit_channel(self, transport: str, channel_id: str) -> Any:
        return await channels.reinit_channel(self, transport, channel_id)

    async def delete_channel(
        self, transport: str, channel_id: str, delete_chats: bool = True
    ) -> Any:
        return await channels.delete_channel(self, transport, channel_id, delete_chats)

    async def list_channels(self) -> Any:
        return await channels.list_channels(self)

    async def generate_templates_link(self, data: TemplatesLinkInput) -> Any:
        return await iframe.generate_templates_link(self, data)

    async def generate_waba_profile_link(self, channel_id: str) -> Any:
        return await iframe.generate_waba_profile_link(self, channel_id)

    async def increase_balance(self, data: BalanceInput) -> Any:
        return await balance.increase_balance(self, data)

    async def get_balance(self) -> Any:
        return await balance.get_balance(self)

    async def get_pricing(self, country_code: str) -> Any:
        return await waba.get_pricing(self, country_code)

    async def get_transactions(self, channel_id: str, date: str) -> Any:
        return await waba.get_transactions(self, channel_id, date)


    async def delete_account(self, account_id: int) -> Any:
        return await accounts.delete_account(self, account_id)

    async def get_waba_summary(self) -> Any:
        return await accounts.get_waba_summary(self)

    async def list_all_transactions(self, date: str) -> Any:
        return await accounts.list_all_transactions(self, date)

    async def generate_chats_link(self, data: dict) -> Any:
        return await iframe.generate_chats_link(self, data)

    async def generate_unanswered_link(self, data: dict) -> Any:
        return await iframe.generate_unanswered_link(self, data)

    async def list_waba_templates(self) -> Any:
        return await waba.list_waba_templates(self)

    async def create_user(self, data: UserInput) -> Any:
        return await users.create_user(self, data)

    async def delete_user(self, user_id: str) -> Any:
        return await users.delete_user(self, user_id)

    async def list_users(self) -> Any:
        return await users.list_users(self)

    async def get_channel_info(self, transport: str, channel_id: str) -> Any:
        return await channels.get_channel_info(self, transport, channel_id)

    async def send_test_webhook(self, uri: str) -> Any:
        return await webhooks.send_test_webhook(self, uri)
