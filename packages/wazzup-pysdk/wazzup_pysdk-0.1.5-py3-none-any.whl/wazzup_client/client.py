"""Developer-friendly Wazzup API client facade over the legacy implementation."""

from __future__ import annotations

from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncIterator, Callable, Dict, Generic, Iterator, List, Mapping, Optional, Sequence, Type, TypeVar, Union, cast, overload

from pydantic import BaseModel, ValidationError

from .legacy_client import WazzupLegacyClient
from .public.schemas import ChannelItem, Contact, Deal, Pipeline, User, WebhooksSettings, WebhookSubscriptions
from .webhook_events import Handler, WebhookEventRouter


ModelT = TypeVar("ModelT", bound=BaseModel)


@dataclass(slots=True)
class ResourceList(Generic[ModelT]):
    """Container for list results with access to typed items and raw payload."""

    items: List[ModelT]
    raw: Any

    def __iter__(self) -> Iterator[ModelT]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int) -> ModelT:
        return self.items[index]


class BaseResource(Generic[ModelT]):
    """Generic CRUD wrapper providing a namespace per API resource."""

    def __init__(
        self,
        legacy: WazzupLegacyClient,
        section: str,
        *,
        model: Optional[Type[ModelT]] = None,
        list_key: Optional[str] = None,
    ):
        self._legacy = legacy
        self._section = section
        self._model = model
        self._list_key = list_key

    def _ensure_callable(self, name: str) -> Any:
        func = getattr(self._legacy, name, None)
        if func is None:
            raise AttributeError(f"Legacy client has no method {name}")
        return func

    def _extract_collection(self, payload: Any) -> Sequence[Dict[str, Any]]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            if self._list_key and isinstance(payload.get(self._list_key), list):
                return cast(Sequence[Dict[str, Any]], payload[self._list_key])
            if "data" in payload and isinstance(payload["data"], list):
                return cast(Sequence[Dict[str, Any]], payload["data"])
        raise TypeError("Unable to extract collection from legacy response")

    def _validate(self, payload: Any) -> ModelT:
        assert self._model is not None  # for type-checkers
        if isinstance(payload, self._model):
            return payload
        if isinstance(payload, dict):
            try:
                return self._model.model_validate(payload)
            except ValidationError as exc:  # pragma: no cover - surfaced to caller
                raise ValueError(
                    f"Failed to parse legacy response for {self._section}: {exc}"
                ) from exc
        raise TypeError(
            f"Expected mapping when parsing {self._section} response, got {type(payload)!r}"
        )

    async def list(self, **params: Any) -> Union[ResourceList[ModelT], Any]:
        """List all items of this resource."""
        func_name = f"list_{self._section}s"
        func = self._ensure_callable(func_name)
        result = await func(**params)
        if self._model is None:
            return result
        collection = self._extract_collection(result)
        items = [self._validate(item) for item in collection]
        return ResourceList(items=items, raw=result)

    async def get(self, id: str) -> Union[ModelT, Any]:
        """Fetch a single resource by identifier."""
        func_name = f"get_{self._section}"
        func = self._ensure_callable(func_name)
        result = await func(id)
        if self._model is None:
            return result
        return self._validate(result)

    async def create(self, **data: Any) -> Union[ModelT, Dict[str, Any]]:
        """Create a new resource instance."""
        func_name = f"create_{self._section}"
        func = self._ensure_callable(func_name)
        result = await func(**data)
        if self._model is None:
            return result
        if isinstance(result, dict) and result:
            try:
                return self._validate(result)
            except (TypeError, ValueError):
                return result
        return result

    async def update(self, id: str, **data: Any) -> Union[ModelT, Dict[str, Any]]:
        """Update an existing resource instance."""
        func_name = f"update_{self._section}"
        func = getattr(self._legacy, func_name, None) or getattr(
            self._legacy, f"create_{self._section}", None
        )
        if func is None:
            raise AttributeError(f"Legacy client has no update/create method for {self._section}")
        result = await func(id=id, **data)
        if self._model is None:
            return result
        if isinstance(result, dict) and result:
            try:
                return self._validate(result)
            except (TypeError, ValueError):
                return result
        return result

    async def delete(self, id: str) -> Dict[str, Any]:
        """Delete a resource by identifier."""
        func_name = f"delete_{self._section}"
        func = self._ensure_callable(func_name)
        result = await func(id)
        return cast(Dict[str, Any], result if result is not None else {})


class TypedResource(BaseResource[ModelT]):
    """Typed resource that guarantees Pydantic objects for common operations."""

    @overload
    async def list(self, **params: Any) -> ResourceList[ModelT]:
        ...

    @overload
    async def list(self, **params: Any) -> Any:  # pragma: no cover - typing fallback
        ...

    async def list(self, **params: Any) -> ResourceList[ModelT]:
        result = await super().list(**params)
        if isinstance(result, ResourceList):
            return result
        raise TypeError("TypedResource.list expected a ResourceList result")

    async def get(self, id: str) -> ModelT:
        result = await super().get(id)
        if isinstance(result, BaseModel):
            return cast(ModelT, result)
        raise TypeError("TypedResource.get expected a BaseModel result")

    async def create(self, **data: Any) -> Union[ModelT, Dict[str, Any]]:
        return await super().create(**data)

    async def update(self, id: str, **data: Any) -> Union[ModelT, Dict[str, Any]]:
        return await super().update(id=id, **data)


class ChannelsResource(TypedResource[ChannelItem]):
    """Additional channel-specific helpers that wrap legacy calls."""

    async def list(self, **_params: Any) -> ResourceList[ChannelItem]:
        """List channels and expose normalized payload via .raw."""
        raw_channels = await self._legacy.list_channels()
        items = [self._validate(item) for item in raw_channels]
        normalized = {"channels": raw_channels, "count": len(raw_channels)}
        return ResourceList(items=items, raw=normalized)

    async def normalized(self) -> Dict[str, Any]:
        """Return channels in the historical dict format."""
        resource = await self.list()
        return cast(Dict[str, Any], resource.raw)

    async def info(self, transport: str, channel_id: str) -> Dict[str, Any]:
        """Fetch detailed information for a channel."""
        return await self._legacy.get_channel_info(transport, channel_id)

    async def create(self, *, transport: str, **data: Any) -> Dict[str, Any]:
        """Create a channel via the tech API."""
        return await self._legacy.create_channel(transport, **data)

    async def reinitialize(self, transport: str, channel_id: str) -> Dict[str, Any]:
        """Reinitialize a channel session."""
        return await self._legacy.reinit_channel(transport, channel_id)

    async def delete(
        self,
        *,
        transport: str,
        channel_id: str,
        delete_chats: bool = True,
    ) -> Dict[str, Any]:
        """Delete a channel via the tech API."""
        return await self._legacy.delete_channel(transport, channel_id, delete_chats)

    async def generate_link(self, payload: Mapping[str, Any]) -> Dict[str, Any]:
        """Generate a channel connection link payload."""
        return await self._legacy.generate_channel_link(payload)

    async def assign_user(
        self,
        user_id: str,
        channel_id: str,
        role: str = "seller",
        allow_get_new_clients: bool = True,
    ) -> Any:
        """Assign a single user to a channel with an optional role."""
        return await self._legacy.assign_user_to_channel(
            user_id=user_id,
            channel_id=channel_id,
            role=role,
            allow_get_new_clients=allow_get_new_clients,
        )

    async def assign_users(self, user_assignments: List[Dict[str, Any]], channel_id: str) -> Any:
        """Assign multiple users to a channel."""
        return await self._legacy.assign_users_to_channel(user_assignments, channel_id=channel_id)

    async def remove_user(self, user_id: str, channel_id: str) -> Any:
        """Remove a user from a channel."""
        result = await self._legacy.remove_user_from_channel(user_id, channel_id)
        return cast(Dict[str, Any], result)


class UsersResource(TypedResource[User]):
    """Typed user resource with raw helpers."""

    async def list_raw(self) -> List[Dict[str, Any]]:
        """Return the raw users payload from the API."""
        return await self._legacy.list_users()

    async def get_raw(self, user_id: str) -> Dict[str, Any]:
        """Fetch raw user data by identifier."""
        return await self._legacy.get_user(user_id)

    async def create_many(self, users: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
        """Bulk create or update users."""
        return await self._legacy.create_users(list(users))


class AccountsResource:
    """Account operations with dedicated helpers."""

    def __init__(self, legacy: WazzupLegacyClient) -> None:
        self._legacy = legacy

    async def create(
        self,
        *,
        name: str,
        lang: str = "ru",
        currency: str = "RUB",
        crm_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new account (partner API key required)."""
        return await self._legacy.create_account(
            name=name,
            lang=lang,
            currency=currency,
            crm_key=crm_key,
        )

    async def get_settings(self) -> Dict[str, Any]:
        """Fetch account settings."""
        return await self._legacy.get_account_settings()

    async def settings(self) -> Dict[str, Any]:
        """Backward compatible alias for get_settings."""
        return await self.get_settings()

    async def update_settings(self, **params: Any) -> Dict[str, Any]:
        return await self._legacy.update_account_settings(**params)

    async def balance(self) -> Dict[str, Any]:
        return await self._legacy.get_balance()

    async def get_balance(self) -> Dict[str, Any]:
        """Backward compatible alias for balance."""
        return await self.balance()

    async def user_roles(self, user_id: str) -> List[Dict[str, Any]]:
        """Return user roles across channels."""
        return await self._legacy.get_user_channel_roles(user_id)


class WebhooksNamespace:
    """Manage webhook API settings and expose a local webhook listener."""

    def __init__(self, legacy: WazzupLegacyClient, *, expected_bearer: Optional[str] = None) -> None:
        self._legacy = legacy
        self.events = WebhookEventRouter()
        if expected_bearer:
            self.events.set_expected_bearer(expected_bearer)

    async def settings(self) -> WebhooksSettings:
        result = await self._legacy.get_webhook_settings()
        return WebhooksSettings.model_validate(result)

    async def update(
        self,
        settings: Union[WebhooksSettings, Mapping[str, Any]],
    ) -> WebhooksSettings:
        payload = self._normalize_settings(settings)
        result = await self._legacy.update_webhook_settings(payload)
        # The API returns {ok} or simple 200 OK, so we return the settings we sent
        return WebhooksSettings.model_validate(payload)

    async def ensure(
        self,
        *,
        uri: str,
        auth_token: Optional[str] = None,
        subscriptions: Union[WebhookSubscriptions, Mapping[str, Any], None] = None,
    ) -> WebhooksSettings:
        payload: Dict[str, Any] = {"webhooksUri": uri}
        if auth_token is not None:
            # Set expected bearer token for incoming webhooks (not sent to API)
            self.expect_bearer(auth_token)
        if subscriptions is not None:
            if isinstance(subscriptions, WebhookSubscriptions):
                payload["subscriptions"] = subscriptions.model_dump(exclude_none=True)
            else:
                payload["subscriptions"] = dict(subscriptions)
        return await self.update(payload)

    async def test(self, uri: str) -> Dict[str, Any]:
        return await self._legacy.test_webhook(uri)

    async def start_listener(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
        path: str = "/webhooks",
        log_level: str = "warning",
        require_bearer: Optional[str] = None,
    ) -> str:
        if require_bearer is not None:
            self.expect_bearer(require_bearer)
        return await self.events.start(
            host=host,
            port=port,
            path=path,
            log_level=log_level,
            expected_bearer=self.events.expected_bearer,
        )

    async def stop_listener(self) -> None:
        await self.events.stop()

    def on(self, event: Union[str, Type[BaseModel]]) -> Callable[[Handler], Handler]:
        return self.events.on(event)

    @property
    def url(self) -> str:
        return self.events.url

    def expect_bearer(self, token: Optional[str]) -> None:
        self.events.set_expected_bearer(token)

    async def close(self) -> None:
        await self.events.stop()

    @staticmethod
    def _normalize_settings(settings: Union[WebhooksSettings, Mapping[str, Any]]) -> Dict[str, Any]:
        if isinstance(settings, WebhooksSettings):
            return settings.model_dump(exclude_none=True)
        if isinstance(settings, Mapping):
            return dict(settings)
        raise TypeError("Webhooks settings must be a mapping or WebhooksSettings model")


class WazzupClient:
    """Modern facade exposing organized namespaces over the legacy API client."""

    def __init__(
        self,
        api_key: str,
        tech_base_url: str = "https://tech.wazzup24.com",
        public_base_url: str = "https://api.wazzup24.com",
        *,
        timeout: Optional[float] = None,
        crm_key: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.crm_key = crm_key
        self._legacy = WazzupLegacyClient(
            api_key=api_key,
            tech_base_url=tech_base_url,
            public_base_url=public_base_url,
            timeout=timeout,
        )

        self.contacts = TypedResource(self._legacy, "contact", model=Contact, list_key="data")
        self.users = UsersResource(self._legacy, "user", model=User)
        self.deals = TypedResource(self._legacy, "deal", model=Deal, list_key="data")
        self.pipelines = TypedResource(self._legacy, "pipeline", model=Pipeline)
        self.accounts = AccountsResource(self._legacy)
        self.channels = ChannelsResource(self._legacy, "channel", model=ChannelItem)
        self.webhooks = WebhooksNamespace(self._legacy, expected_bearer=crm_key)

    async def close(self) -> None:
        """Release underlying client resources."""
        await self.webhooks.close()
        await self._legacy.close()

    async def __aenter__(self) -> "WazzupClient":
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    def __repr__(self) -> str:
        namespaces = "contacts, users, deals, channels, pipelines, accounts, webhooks"
        return f"<WazzupClient api_key={self.api_key[:6]}... namespaces=[{namespaces}]>"


@asynccontextmanager
async def wazzup_client_context(
    api_key: str,
    *,
    tech_base_url: str = "https://tech.wazzup24.com",
    public_base_url: str = "https://api.wazzup24.com",
    timeout: Optional[float] = None,
    crm_key: Optional[str] = None,
) -> AsyncIterator[WazzupClient]:
    """Async context manager that yields a WazzupClient and closes it automatically."""
    client = WazzupClient(
        api_key=api_key,
        tech_base_url=tech_base_url,
        public_base_url=public_base_url,
        timeout=timeout,
        crm_key=crm_key,
    )
    try:
        yield client
    finally:
        await client.close()
