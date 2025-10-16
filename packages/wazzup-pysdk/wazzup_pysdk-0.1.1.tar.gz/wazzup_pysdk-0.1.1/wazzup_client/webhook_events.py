"""Runtime utilities for handling Wazzup webhook events."""

from __future__ import annotations

import asyncio
import inspect
from collections import defaultdict
from typing import Any, Awaitable, Callable, Dict, Iterable, List, Mapping, Optional, Tuple, Type, Union

from pydantic import BaseModel, ValidationError

from .public.schemas import (
    ChannelsUpdatesWebhook,
    CreateEntitiesWebhook,
    MessagesWebhook,
    StatusesWebhook,
    TemplateStatusWebhook,
)

EventModel = Type[BaseModel]
EventPayload = BaseModel
Handler = Callable[[EventPayload], Awaitable[Any]]
EventKey = Union[str, EventModel]

_EVENT_MODEL_REGISTRY: Dict[str, EventModel] = {
    "messages": MessagesWebhook,
    "statuses": StatusesWebhook,
    "createEntities": CreateEntitiesWebhook,
    "channelsUpdates": ChannelsUpdatesWebhook,
    "templateStatus": TemplateStatusWebhook,
}

_MODEL_TO_EVENT: Dict[EventModel, str] = {model: name for name, model in _EVENT_MODEL_REGISTRY.items()}


class AuthorizationError(Exception):
    """Raised when webhook authorization fails."""


class WebhookEventRouter:
    """Register coroutine handlers for webhook payloads and expose a FastAPI listener."""

    def __init__(self) -> None:
        self._handlers: Dict[str, List[Handler]] = defaultdict(list)
        self._wildcard_handlers: List[Handler] = []
        self._lock = asyncio.Lock()
        self._app: Any = None
        self._server: Any = None
        self._task: Optional[asyncio.Task[None]] = None
        self._host: str = "0.0.0.0"
        self._port: Optional[int] = None
        self._path: str = "/webhooks"
        self._expected_bearer: Optional[str] = None

    # region Registration helpers

    def register(self, event: EventKey, handler: Handler) -> None:
        """Register a coroutine handler for the given event key."""
        if not inspect.iscoroutinefunction(handler):
            raise TypeError("Webhook handlers must be defined as async functions")

        event_name = self._normalize_event(event)
        if event_name == "*":
            self._wildcard_handlers.append(handler)
            return

        self._handlers[event_name].append(handler)

    def on(self, event: EventKey) -> Callable[[Handler], Handler]:
        """Decorator to register a coroutine handler for a webhook event."""

        def decorator(func: Handler) -> Handler:
            self.register(event, func)
            return func

        return decorator

    # endregion

    # region Server lifecycle

    async def start(
        self,
        *,
        host: str = "0.0.0.0",
        port: int = 8080,
        path: str = "/webhooks",
        log_level: str = "warning",
        expected_bearer: Optional[str] = None,
    ) -> str:
        """Start an embedded FastAPI+Uvicorn server to receive webhook callbacks."""
        async with self._lock:
            if self.is_running:
                raise RuntimeError("Webhook listener already running")

            try:
                from fastapi import FastAPI, HTTPException, Header
            except ImportError as exc:  # pragma: no cover - runtime guard
                raise RuntimeError(
                    "FastAPI is not installed. Install the 'webhooks' extra: pip install wazzup-pysdk[webhooks]"
                ) from exc

            try:
                import uvicorn
            except ImportError as exc:  # pragma: no cover - runtime guard
                raise RuntimeError(
                    "uvicorn is not installed. Install the 'webhooks' extra: pip install wazzup-pysdk[webhooks]"
                ) from exc

            self._host = host
            self._port = port
            self._path = path
            if expected_bearer is not None:
                self.set_expected_bearer(expected_bearer)

            app = FastAPI()

            @app.post(path)
            async def webhook_endpoint(
                payload: Dict[str, Any],
                authorization: Optional[str] = Header(default=None),
            ) -> Dict[str, str]:
                try:
                    await self._handle_request(payload, authorization)
                except AuthorizationError as exc:
                    raise HTTPException(status_code=401, detail=str(exc)) from exc
                except ValidationError as exc:
                    raise HTTPException(status_code=422, detail=exc.errors()) from exc
                return {"status": "ok"}

            config = uvicorn.Config(
                app,
                host=host,
                port=port,
                log_level=log_level,
                loop="asyncio",
                lifespan="auto",
            )
            server = uvicorn.Server(config)
            task = asyncio.create_task(server.serve())

            self._app = app
            self._server = server
            self._task = task

        while self._server and not self._server.started and not self._task.done():
            await asyncio.sleep(0.05)

        if self._task and self._task.done():
            exception = self._task.exception()
            await self.stop()
            if exception:
                raise exception

        return self.url

    async def stop(self) -> None:
        """Stop the webhook listener if it is running."""
        async with self._lock:
            if not self._task:
                return

            if self._server:
                self._server.should_exit = True

        if self._task:
            try:
                await self._task
            finally:
                self._task = None
                self._server = None
                self._app = None

    # endregion

    # region Inspection helpers

    @property
    def is_running(self) -> bool:
        return bool(self._task) and not self._task.done()

    @property
    def url(self) -> str:
        if self._port is None:
            raise RuntimeError("Webhook listener has not been started")
        return f"http://{self._host}:{self._port}{self._path}"

    @property
    def expected_bearer(self) -> Optional[str]:
        return self._expected_bearer

    # endregion

    # region Dispatch helpers

    async def dispatch(self, payload: Mapping[str, Any]) -> None:
        """Manually dispatch a payload to registered handlers (useful for tests)."""
        await self._dispatch(dict(payload))

    async def _handle_request(self, payload: Mapping[str, Any], authorization: Optional[str]) -> None:
        self._check_authorization(authorization)
        await self._dispatch(payload)

    async def _dispatch(self, payload: Mapping[str, Any]) -> None:
        event_name, model = self._identify_event(payload)
        handlers: Iterable[Handler]
        typed_payload: Union[BaseModel, Mapping[str, Any]]

        if model:
            typed_payload = model.model_validate(payload)
            handlers = self._handlers.get(event_name, [])
        else:
            typed_payload = payload
            handlers = ()

        normalized_payload = typed_payload if model else payload

        dispatch_tasks = [
            handler(normalized_payload) for handler in handlers
        ]
        dispatch_tasks.extend(handler(normalized_payload) for handler in self._wildcard_handlers)

        if dispatch_tasks:
            await asyncio.gather(*dispatch_tasks)

    def _identify_event(self, payload: Mapping[str, Any]) -> Tuple[str, Optional[EventModel]]:
        if "messages" in payload:
            return "messages", _EVENT_MODEL_REGISTRY["messages"]
        if "statuses" in payload:
            return "statuses", _EVENT_MODEL_REGISTRY["statuses"]
        if "channelsUpdates" in payload:
            return "channelsUpdates", _EVENT_MODEL_REGISTRY["channelsUpdates"]
        if "templateStatus" in payload:
            return "templateStatus", _EVENT_MODEL_REGISTRY["templateStatus"]
        if "createContact" in payload or "createDeal" in payload:
            return "createEntities", _EVENT_MODEL_REGISTRY["createEntities"]
        return "*", None

    def _normalize_event(self, event: EventKey) -> str:
        if isinstance(event, str):
            if event != "*" and event not in _EVENT_MODEL_REGISTRY:
                raise KeyError(f"Unknown webhook event '{event}'")
            return event

        if inspect.isclass(event) and issubclass(event, BaseModel):
            try:
                return _MODEL_TO_EVENT[event]
            except KeyError as exc:
                raise KeyError(f"Model {event.__name__} is not a supported webhook payload") from exc

        raise TypeError("Event key must be a string name or a webhook payload model")

    # endregion

    # region Authorization helpers

    def set_expected_bearer(self, token: Optional[str]) -> None:
        if token:
            self._expected_bearer = token.strip()
        else:
            self._expected_bearer = None

    def _check_authorization(self, authorization: Optional[str]) -> None:
        if self._expected_bearer is None:
            return
        if authorization != f"Bearer {self._expected_bearer}":
            raise AuthorizationError("Invalid or missing Authorization header")

    # endregion
