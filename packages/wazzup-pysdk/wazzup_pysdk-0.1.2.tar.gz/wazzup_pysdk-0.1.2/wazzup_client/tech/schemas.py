"""Pydantic schemas for the tech partner Wazzup API."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import AnyUrl, BaseModel, ConfigDict

from .._compat import constr

__all__ = (
    "AccountCreate",
    "AccountCreateResponse",
    "BalanceChange",
    "BalanceInfo",
    "ChannelCreateResponse",
    "ChannelDeleteRequest",
    "ChannelDetails",
    "ChannelsListItem",
    "ChannelsListResponse",
    "ChannelsListSubscription",
    "ChannelCreate",
    "GenerateChannelLinkRequest",
    "GenerateChannelLinkResponse",
    "GenerateTemplatesLinkRequest",
    "GenerateTemplatesLinkResponse",
    "GenerateWabaProfileLinkRequest",
    "GenerateChatsLinkRequest",
    "GenerateChatsLinkResponse",
    "GenerateUnansweredLinkRequest",
    "GenerateUnansweredLinkResponse",
    "IFrameRequest",
    "SettingsPatch",
    "TechUser",
    "UserRoleItem",
    "WabaPricingEntry",
    "WabaPricingResponse",
    "WabaSummaryItem",
    "WabaTemplate",
    "WabaTransactionItem",
    "WabaTransactionsResponse",
    "WebhookTestRequest",
)


class AccountCreate(BaseModel):
    crmKey: constr(strip_whitespace=True, min_length=16)
    name: constr(strip_whitespace=True, min_length=1)
    lang: constr(strip_whitespace=True, regex=r"^(ru|en|es|pt)$")
    currency: constr(strip_whitespace=True, regex=r"^(RUR|EUR|USD|KZT)$")


class AccountCreateResponse(BaseModel):
    accountId: int
    apiKey: constr(strip_whitespace=True, min_length=16)


class UserRoleItem(BaseModel):
    channelId: str
    userId: str
    role: constr(strip_whitespace=True, regex=r"^(auditor|manager|seller)$")
    allowGetNewClients: bool


class SettingsPatch(BaseModel):
    pushInputOutputMessageEventsForManagers: Optional[bool] = None
    userRoles: Optional[List[UserRoleItem]] = None


class ChannelCreate(BaseModel):
    transport: Optional[constr(strip_whitespace=True)] = None
    credentials: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra="allow")


class GenerateChannelLinkRequest(BaseModel):
    transport: constr(strip_whitespace=True, regex=r"^(whatsapp|viber|telegram|tgapi|instAPI|wapi)$")
    channelId: Optional[str] = None


class GenerateChannelLinkResponse(BaseModel):
    link: AnyUrl


class ChannelCreateResponse(BaseModel):
    url: Optional[AnyUrl] = None


class ChannelDeleteRequest(BaseModel):
    deleteChats: bool = True


class ChannelsListSubscription(BaseModel):
    balance: Optional[int] = None
    channelsQtyTotal: Optional[int] = None
    guid: Optional[str] = None
    name: Optional[str] = None
    state: Optional[str] = None
    tariff: Optional[str] = None
    type: Optional[str] = None


class ChannelDetails(BaseModel):
    proxy: Optional[Dict[str, str]] = None
    commentsFilter: Optional[List[str]] = None
    instAPI: Optional[bool] = None
    vkGroupId: Optional[int] = None
    subscription: Optional[ChannelsListSubscription] = None
    notifications: Optional[List[Dict[str, str]]] = None
    autoMessage: Optional[Dict[str, str]] = None
    comments: Optional[Dict[str, str]] = None
    approachingDialogueLimit: Optional[bool] = None
    dialogLimitExceeded: Optional[bool] = None
    isTrial: Optional[bool] = None
    endOfTrial: Optional[datetime] = None
    initUrl: Optional[AnyUrl] = None


class ChannelsListItem(BaseModel):
    deleted: bool
    details: Optional[ChannelDetails] = None
    guid: str
    hasAccess: bool
    name: Optional[str] = None
    phone: Optional[str] = None
    state: str
    transport: str
    visible: bool
    tier: Optional[str] = None


class ChannelsListResponse(BaseModel):
    channels: List[ChannelsListItem]
    count: int


class GenerateTemplatesLinkRequest(BaseModel):
    type: constr(strip_whitespace=True, regex=r"^(wabaTemplate|wazzupTemplate)$")


class GenerateTemplatesLinkResponse(BaseModel):
    link: AnyUrl


class GenerateWabaProfileLinkRequest(BaseModel):
    channelId: str


class IFrameRequest(BaseModel):
    transport: constr(strip_whitespace=True, min_length=1)
    redirectUri: Optional[AnyUrl] = None
    channelId: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class BalanceChange(BaseModel):
    accountId: int
    value: int


class BalanceInfo(BaseModel):
    currency: constr(strip_whitespace=True, regex=r"^(RUR|EUR|USD|KZT)$")
    balance: int


class WabaPricingEntry(BaseModel):
    USD: float
    EUR: float
    RUB: float
    KZT: float


class WabaPricingResponse(BaseModel):
    timestamp: datetime
    pricing: Dict[
        constr(strip_whitespace=True, regex=r"^(marketing|utility|authentication|service)$"),
        WabaPricingEntry,
    ]


class WabaTransactionItem(BaseModel):
    waba_id: str
    channel_id: str
    template_type: constr(strip_whitespace=True, regex=r"^(MARKETING|UTILITY|AUTHENTICATION|SERVICE)$")
    amount: float
    currency: constr(strip_whitespace=True, regex=r"^(USD|EUR|RUB|KZT)$")
    recipient_phone: constr(regex=r"^\d{8,15}$")
    session_date: datetime
    billing_country: constr(min_length=2, max_length=2)


class WabaTransactionsResponse(BaseModel):
    transactions: List[WabaTransactionItem]
    count: int


class GenerateChatsLinkRequest(BaseModel):
    userId: Optional[str] = None
    dealId: Optional[str] = None


class GenerateChatsLinkResponse(BaseModel):
    link: AnyUrl


class GenerateUnansweredLinkRequest(BaseModel):
    userId: Optional[str] = None


class GenerateUnansweredLinkResponse(BaseModel):
    link: AnyUrl


class WabaTemplate(BaseModel):
    templateGuid: str
    name: str
    status: str
    category: str
    language: str
    body: str


class WabaSummaryItem(BaseModel):
    accountId: int
    name: str
    balance: int
    spent: int
    currency: str


class TechUser(BaseModel):
    id: str
    name: str
    allowGetNewClients: bool = False
    role: Literal["auditor", "manager", "seller"]


class WebhookTestRequest(BaseModel):
    webhooksUri: AnyUrl
