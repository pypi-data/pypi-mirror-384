"""Async client for the public Wazzup API."""

from __future__ import annotations

from typing import Any, Iterable, Mapping, Union

from ..base_client import BaseWazzupClient
from .endpoints import channels, contacts, counters, deals, iframe, messages, pipelines, users, webhooks
from .schemas import Contact, Deal, IFrameRequest, MessageSendRequest, Pipeline, User

MappingLike = Mapping[str, Any]

UserInput = Union[User, MappingLike]
ContactInput = Union[Contact, MappingLike]
DealInput = Union[Deal, MappingLike]
PipelineInput = Union[Pipeline, MappingLike]
MessageInput = Union[MessageSendRequest, MappingLike]
IFrameInput = Union[IFrameRequest, MappingLike]


class WazzupPublicClient(BaseWazzupClient):
    """Client for https://api.wazzup24.com/v3/"""

    async def get_users(self) -> Any:
        return await users.get_users(self)

    async def get_user(self, user_id: str) -> Any:
        return await users.get_user(self, user_id)

    async def post_users(self, user_list: Iterable[UserInput]) -> Any:
        return await users.post_users(self, user_list)

    async def delete_user(self, user_id: str) -> Any:
        return await users.delete_user(self, user_id)

    async def bulk_delete_users(self, user_ids: Iterable[str]) -> Any:
        return await users.bulk_delete_users(self, user_ids)

    async def create_contact(self, contact: ContactInput) -> Any:
        return await contacts.create_contacts(self, [contact])

    async def create_contacts(self, contact_list: Iterable[ContactInput]) -> Any:
        return await contacts.create_contacts(self, contact_list)

    async def get_contacts(self, offset: int = 0) -> Any:
        return await contacts.get_contacts(self, offset)

    async def get_contact(self, contact_id: str) -> Any:
        return await contacts.get_contact(self, contact_id)

    async def delete_contact(self, contact_id: str) -> Any:
        return await contacts.delete_contact(self, contact_id)

    async def bulk_delete_contacts(self, contact_ids: Iterable[str]) -> Any:
        return await contacts.bulk_delete_contacts(self, contact_ids)

    async def post_deals(self, deals_list: Iterable[DealInput]) -> Any:
        return await deals.create_or_update_deals(self, deals_list)

    async def get_deals(self, offset: int = 0) -> Any:
        return await deals.get_deals(self, offset)

    async def get_deal(self, deal_id: str) -> Any:
        return await deals.get_deal(self, deal_id)

    async def delete_deal(self, deal_id: str) -> Any:
        return await deals.delete_deal(self, deal_id)

    async def bulk_delete_deals(self, deal_ids: Iterable[str]) -> Any:
        return await deals.bulk_delete_deals(self, deal_ids)

    async def post_pipelines(self, pipelines_list: Iterable[PipelineInput]) -> Any:
        return await pipelines.post_pipelines(self, pipelines_list)

    async def get_pipelines(self) -> Any:
        return await pipelines.get_pipelines(self)

    async def patch_webhooks(self, data: MappingLike) -> Any:
        return await webhooks.patch_webhooks(self, data)

    async def get_webhooks_settings(self) -> Any:
        return await webhooks.get_webhooks_settings(self)

    async def send_message(self, msg: MessageInput) -> Any:
        return await messages.send_message(self, msg)

    async def edit_message(self, message_id: str, data: MappingLike) -> Any:
        return await messages.edit_message(self, message_id, data)

    async def delete_message(self, message_id: str) -> Any:
        return await messages.delete_message(self, message_id)

    async def get_unanswered(self, user_id: str) -> Any:
        return await counters.get_unanswered(self, user_id)

    async def get_channels(self) -> Any:
        return await channels.get_channels(self)

    async def generate_iframe_link(self, data: IFrameInput) -> Any:
        return await iframe.generate_iframe_link(self, data)
