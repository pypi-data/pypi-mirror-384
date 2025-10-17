import asyncio
from datetime import datetime, timezone

import pytest

from wazzup_client.public.schemas import MessagesWebhook, StatusesWebhook
from wazzup_client.webhook_events import (
    AuthorizationError,
    WebhookEventRouter,
    identify_webhook_event,
    parse_webhook_payload,
)


def _make_message_payload() -> dict:
    now = datetime.now(tz=timezone.utc).isoformat()
    return {
        "messages": [
            {
                "messageId": "m-1",
                "channelId": "ch-1",
                "chatType": "telegram",
                "chatId": "chat-1",
                "dateTime": now,
                "type": "text",
                "isEcho": False,
                "status": "inbound",
                "text": "hello",
                "contact": {
                    "id": "contact-1",
                },
            }
        ]
    }


@pytest.mark.asyncio
async def test_dispatch_typed_event():
    router = WebhookEventRouter()
    received: list[MessagesWebhook] = []
    wildcards: list[MessagesWebhook] = []

    @router.on("messages")
    async def handle_messages(event: MessagesWebhook) -> None:
        received.append(event)

    @router.on("*")
    async def handle_any(event: dict) -> None:
        wildcards.append(event)

    await router.dispatch(_make_message_payload())

    assert len(received) == 1
    assert received[0].messages[0].messageId == "m-1"
    assert wildcards and isinstance(wildcards[0], MessagesWebhook)
    assert wildcards[0].messages[0].text == "hello"


@pytest.mark.asyncio
async def test_register_with_model_type():
    router = WebhookEventRouter()
    event_ids: list[str] = []

    @router.on(StatusesWebhook)
    async def handle_status(event: StatusesWebhook) -> None:
        event_ids.append(event.statuses[0].messageId)

    payload = {
        "statuses": [
            {
                "messageId": "m-2",
                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                "status": "sent",
            }
        ]
    }

    await router.dispatch(payload)

    assert event_ids == ["m-2"]


def test_register_unknown_event_raises():
    router = WebhookEventRouter()

    async def handler(event):  # pragma: no cover - helper
        return event

    with pytest.raises(KeyError):
        router.register("unknownEvent", handler)


def test_register_non_async_handler_raises():
    router = WebhookEventRouter()

    with pytest.raises(TypeError):
        router.register("messages", lambda _: None)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_start_and_stop_listener(monkeypatch):
    pytest.importorskip("fastapi")
    uvicorn_module = pytest.importorskip("uvicorn")

    # Keep real Config but replace Server with a controllable stub
    class StubServer:
        def __init__(self, config: uvicorn_module.Config) -> None:
            self.config = config
            self.should_exit = False
            self.started = False

        async def serve(self) -> None:
            self.started = True
            while not self.should_exit:
                await asyncio.sleep(0.01)

    monkeypatch.setattr(uvicorn_module, "Server", StubServer)

    router = WebhookEventRouter()
    url = await router.start(host="127.0.0.1", port=9100, path="/hook-test", log_level="error")

    assert url == "http://127.0.0.1:9100/hook-test"
    assert router.is_running

    await router.stop()
    assert not router.is_running


@pytest.mark.asyncio
async def test_authorization_header_validation():
    router = WebhookEventRouter()
    router.set_expected_bearer("crm_secret")

    payload = _make_message_payload()

    with pytest.raises(AuthorizationError):
        await router._handle_request(payload, authorization=None)

    with pytest.raises(AuthorizationError):
        await router._handle_request(payload, authorization="Bearer wrong")

    await router._handle_request(payload, authorization="Bearer crm_secret")


def test_parse_webhook_payload_returns_typed_model():
    parsed = parse_webhook_payload(_make_message_payload())

    assert parsed.name == "messages"
    assert parsed.is_typed
    assert parsed.payload.messages[0].text == "hello"  # type: ignore[union-attr]


def test_identify_unknown_webhook_event():
    name, model = identify_webhook_event({"something": "else"})

    assert name == "*"
    assert model is None


def test_parsed_webhook_to_dict_serialization():
    """Test that ParsedWebhook can be converted to JSON-serializable dict."""
    import json
    
    parsed = parse_webhook_payload(_make_message_payload())
    
    # Test that direct JSON serialization fails
    with pytest.raises(TypeError, match="Object of type MessagesWebhook is not JSON serializable"):
        json.dumps(parsed.payload)
    
    # Test that to_dict() works
    serializable_data = parsed.to_dict()
    json_string = json.dumps(serializable_data)
    
    # Verify it can be parsed back
    parsed_back = json.loads(json_string)
    assert parsed_back["messages"][0]["text"] == "hello"
    assert parsed_back["messages"][0]["contact"]["id"] == "contact-1"
