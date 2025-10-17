"""Pydantic schemas for the public Wazzup API."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyUrl, BaseModel, Field, FieldValidationInfo, conlist, field_validator, model_validator

from .._compat import constr

__all__ = (
    "ButtonsMatrix",
    "ButtonsObject",
    "ChannelItem",
    "Contact",
    "ContactData",
    "CreateContactPayload",
    "CreateDealPayload",
    "CreateEntitiesWebhook",
    "Deal",
    "IFrameFilter",
    "IFrameOptions",
    "IFrameRequest",
    "IFrameResponse",
    "IFrameUser",
    "MessageButton",
    "MessageSendRequest",
    "MessageSendResponse",
    "MessagesWebhook",
    "Pipeline",
    "PipelineStage",
    "StatusError",
    "StatusItem",
    "StatusesWebhook",
    "TemplateStatusWebhook",
    "UnansweredResponse",
    "User",
    "WebhookContact",
    "WebhookError",
    "WebhookMessageItem",
    "WebhookSubscriptions",
    "WebhooksSettings",
)


class User(BaseModel):
    id: constr(strip_whitespace=True, max_length=64)
    name: constr(strip_whitespace=True, max_length=150)
    phone: Optional[constr(strip_whitespace=True, regex=r"^\d{8,15}$")] = None


class ContactData(BaseModel):
    chatType: constr(
        strip_whitespace=True,
        to_lower=False,
        regex=r"^(whatsapp|whatsgroup|viber|instagram|telegram|telegroup|vk|avito|max|maxgroup)$",
    )
    chatId: Optional[str] = None
    username: Optional[constr(strip_whitespace=True, min_length=1)] = None
    phone: Optional[constr(regex=r"^\d{8,15}$")] = None

    @field_validator("chatId")
    @classmethod
    def validate_chat_id(cls, value: Optional[str], info: FieldValidationInfo) -> Optional[str]:
        chat_type = (info.data or {}).get("chatType")
        if chat_type in {"whatsapp", "viber"} and value:
            if not re.fullmatch(r"^\d{8,15}$", value):
                raise ValueError("chatId для whatsapp/viber — только цифры в международном формате")
        if chat_type == "instagram" and value and value.startswith("@"):
            raise ValueError("instagram chatId передаётся без '@'")
        return value

    @field_validator("phone")
    @classmethod
    def validate_phone_for_transport(cls, value: Optional[str], info: FieldValidationInfo) -> Optional[str]:
        chat_type = (info.data or {}).get("chatType")
        if value and chat_type not in {"telegram", "max"}:
            raise ValueError("phone разрешён только для chatType telegram/max")
        return value


class Contact(BaseModel):
    id: constr(max_length=100)
    responsibleUserId: constr(max_length=100)
    name: constr(max_length=200)
    contactData: conlist(ContactData, min_length=1)
    uri: Optional[constr(max_length=200)] = None


class Deal(BaseModel):
    id: constr(max_length=100)
    responsibleUserId: constr(max_length=100)
    name: constr(max_length=200)
    contacts: conlist(constr(max_length=100), min_length=1, max_length=10)
    uri: constr(max_length=200)
    closed: Optional[bool] = None


class PipelineStage(BaseModel):
    id: constr(max_length=100)
    name: constr(max_length=100)


class Pipeline(BaseModel):
    id: constr(max_length=100)
    name: constr(max_length=100)
    stages: Optional[conlist(PipelineStage, min_length=1)] = None


class ChannelItem(BaseModel):
    channelId: str
    transport: constr(
        strip_whitespace=True,
        regex=r"^(whatsapp|instagram|max|tgapi|wapi|telegram|vk|avito|viber)$",
    )
    plainId: Optional[str] = None
    state: constr(
        strip_whitespace=True,
        regex=(
            r"^(active|init|disabled|phoneUnavailable|qridle|openelsewhere|"
            r"notEnoughMoney|foreignphone|unauthorized|waitForCode|waitForPassword|"
            r"blocked|onModeration|rejected)$"
        ),
    )


class MessageButton(BaseModel):
    text: Optional[constr(max_length=64)] = None
    type: Optional[constr(strip_whitespace=True, regex=r"^text$")] = None
    payload: Optional[str] = None
    url: Optional[AnyUrl] = None
    callbackData: Optional[constr(min_length=1, max_length=64)] = None


ButtonsMatrix = List[List[MessageButton]]


class ButtonsObject(BaseModel):
    replyMarkup: Optional[constr(strip_whitespace=True, regex=r"^(inline|reply)$")] = None
    buttons: Optional[Union[List[MessageButton], ButtonsMatrix]] = None
    removeKeyboard: Optional[bool] = None
    oneTimeKeyboard: Optional[bool] = None

    @model_validator(mode="after")
    def validate_buttons_structure(self) -> "ButtonsObject":
        if not self.buttons:
            return self
        if isinstance(self.buttons, list) and all(isinstance(row, list) for row in self.buttons):
            for row in self.buttons:
                for button in row:
                    if not isinstance(button, MessageButton):
                        raise ValueError("buttons матрица должна содержать MessageButton")
        elif isinstance(self.buttons, list):
            for button in self.buttons:
                if not isinstance(button, MessageButton):
                    raise ValueError("buttons должен содержать MessageButton элементы")
        return self


class MessageSendRequest(BaseModel):
    channelId: str
    chatType: constr(
        strip_whitespace=True,
        regex=r"^(whatsapp|whatsgroup|viber|instagram|telegram|telegroup|vk|avito|max|maxgroup)$",
    )
    chatId: Optional[str] = None
    text: Optional[str] = None
    contentUri: Optional[AnyUrl] = None
    refMessageId: Optional[str] = None
    crmUserId: Optional[str] = None
    crmMessageId: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[constr(regex=r"^\d{8,15}$")] = None
    clearUnanswered: Optional[bool] = None
    templateId: Optional[str] = None
    templateValues: Optional[List[str]] = None
    buttonsObject: Optional[ButtonsObject] = None

    @field_validator("chatId")
    @classmethod
    def validate_chat_id(cls, value: Optional[str], info: FieldValidationInfo) -> Optional[str]:
        chat_type = (info.data or {}).get("chatType")
        if chat_type in {"whatsapp", "viber"} and value and not re.fullmatch(r"^\d{8,15}$", value):
            raise ValueError("chatId для whatsapp/viber — только цифры в международном формате")
        if chat_type == "instagram" and value and value.startswith("@"):
            raise ValueError("instagram chatId передаётся без '@'")
        return value

    @model_validator(mode="after")
    def validate_payload(self) -> "MessageSendRequest":
        has_body = any((self.text, self.contentUri, self.templateId, self.buttonsObject))
        if not has_body:
            raise ValueError("Нужно указать text ИЛИ contentUri ИЛИ templateId / interactive payload")
        if self.text and self.contentUri:
            raise ValueError("Нельзя одновременно передавать text и contentUri")
        return self


class MessageSendResponse(BaseModel):
    messageId: str
    chatId: Optional[str] = None


class WebhookSubscriptions(BaseModel):
    messagesAndStatuses: Optional[bool] = None
    contactsAndDealsCreation: Optional[bool] = None
    channelsUpdates: Optional[bool] = None
    templateStatus: Optional[bool] = None


class WebhooksSettings(BaseModel):
    webhooksUri: AnyUrl
    webhooksAuthToken: Optional[str] = None
    subscriptions: Optional[WebhookSubscriptions] = None


class WebhookContact(BaseModel):
    id: Optional[str] = None
    responsibleUserId: Optional[str] = None
    name: Optional[str] = None
    avatar: Optional[str] = None
    contactData: Optional[List[ContactData]] = None


class WebhookError(BaseModel):
    code: str
    message: Optional[str] = None
    traceId: Optional[str] = None


class QuotedMessage(BaseModel):
    messageId: str
    authorId: Optional[str] = None
    authorName: Optional[str] = None
    text: Optional[str] = None


class WebhookMessageItem(BaseModel):
    messageId: str
    channelId: str
    chatType: constr(
        strip_whitespace=True,
        regex=r"^(whatsapp|whatsgroup|viber|instagram|telegram|telegroup|vk|avito|max|maxgroup)$",
    )
    chatId: str
    avitoProfileId: Optional[str] = None
    dateTime: datetime
    type: constr(
        strip_whitespace=True,
        regex=(
            r"^(text|image|audio|video|document|vcard|geo|wapi_template|"
            r"unsupported|missing_call|unknown)$"
        ),
    )
    isEcho: bool
    contact: Optional[WebhookContact] = None
    text: Optional[str] = None
    contentUri: Optional[AnyUrl] = None
    status: constr(strip_whitespace=True, regex=r"^(sent|delivered|read|error|inbound)$")
    error: Optional[WebhookError] = None
    authorName: Optional[str] = None
    authorId: Optional[str] = None
    quotedMessage: Optional[QuotedMessage] = None
    sentFromApp: Optional[bool] = None
    isEdited: Optional[bool] = None
    isDeleted: Optional[bool] = None
    oldInfo: Optional[Dict[str, Any]] = None
    instPost: Optional[Dict[str, Any]] = None
    interactive: Optional[List[Dict[str, Any]]] = None


class MessagesWebhook(BaseModel):
    messages: List[WebhookMessageItem]


class StatusError(BaseModel):
    error: str
    description: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class StatusItem(BaseModel):
    messageId: str
    timestamp: datetime
    status: constr(strip_whitespace=True, regex=r"^(sent|delivered|read|error|edited)$")
    error: Optional[StatusError] = None


class StatusesWebhook(BaseModel):
    statuses: List[StatusItem]


class CreateContactPayload(BaseModel):
    responsibleUserId: str
    name: Optional[str] = None
    contactData: List[ContactData]
    source: constr(strip_whitespace=True, regex=r"^(auto|byUser)$")


class CreateDealPayload(BaseModel):
    responsibleUserId: str
    contacts: List[str]
    source: constr(strip_whitespace=True, regex=r"^(auto|byUser)$")


class CreateEntitiesWebhook(BaseModel):
    createContact: Optional[CreateContactPayload] = None
    createDeal: Optional[CreateDealPayload] = None


class ChannelUpdateItem(BaseModel):
    channelId: str
    state: constr(
        strip_whitespace=True,
        regex=(
            r"^(qr|qridle|active|disabled|notEnoughMoney|unauthorized|"
            r"openElsewhere|phoneUnavailable|waitForCode)$"
        ),
    )
    tier: Optional[constr(strip_whitespace=True, regex=r"^TIER_(0|1K|10K|100K|UNLIMITED)$")] = None
    qr: Optional[str] = Field(default=None, description="Base64 data URL")
    timestamp: int


class ChannelsUpdatesWebhook(BaseModel):
    channelsUpdates: List[ChannelUpdateItem]


class TemplateStatusWebhook(BaseModel):
    templateStatus: Dict[str, Any]


class UnansweredResponse(BaseModel):
    counterV2: int
    type: Optional[constr(strip_whitespace=True, regex=r"^(red|grey)$")] = None
    lastMsgDateTime: Optional[datetime] = None


class IFrameUser(BaseModel):
    """User information for iframe request."""
    id: constr(strip_whitespace=True, min_length=1)
    name: constr(strip_whitespace=True, min_length=1)


class IFrameFilter(BaseModel):
    """Filter for iframe request to show specific chats."""
    chatType: constr(
        strip_whitespace=True,
        regex=r"^(whatsapp|whatsgroup|viber|instagram|telegram|telegroup|vk|avito|max|maxgroup)$"
    )
    chatId: Optional[str] = None
    name: Optional[str] = None


class IFrameOptions(BaseModel):
    """Options for iframe events."""
    clientType: Optional[str] = None
    useDealsEvents: Optional[bool] = None
    useMessageEvents: Optional[bool] = None


class IFrameRequest(BaseModel):
    """Request model for iframe link generation."""
    user: IFrameUser
    scope: constr(strip_whitespace=True, regex=r"^(global|card)$")
    filter: Optional[List[IFrameFilter]] = None
    activeChat: Optional[Dict[str, Any]] = None
    options: Optional[IFrameOptions] = None

    @model_validator(mode="after")
    def validate_scope_and_filter(self) -> "IFrameRequest":
        if self.scope == "card" and not self.filter:
            raise ValueError("filter is required when scope is 'card'")
        return self


class IFrameResponse(BaseModel):
    """Response model for iframe link generation."""
    url: AnyUrl
