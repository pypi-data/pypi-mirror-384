Wazzup Python SDK
=================

An asynchronous, developer-friendly Python client for the Wazzup public and tech APIs. The package modernises the legacy client by offering typed namespaces, predictable CRUD-style methods, and optional webhook handling utilities.

Table of Contents
-----------------
1. [Features](#features)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Architecture and Legacy Compatibility](#architecture-and-legacy-compatibility)
5. [Resource Namespaces](#resource-namespaces)
6. [Working with Responses](#working-with-responses)
7. [Async Usage Patterns](#async-usage-patterns)
8. [Configuration Helpers](#configuration-helpers)
9. [Testing](#testing)
10. [Project Structure](#project-structure)
11. [Contributing](#contributing)
12. [Webhook Listener](#webhook-listener)
13. [License](#license)

Features
--------
- Async-first API built on `httpx`.
- Typed accessors for key resources (`contacts`, `users`, `deals`, `channels`, `pipelines`, `accounts`, `webhooks`).
- Automatic fallback to legacy methods to preserve backwards compatibility.
- Pydantic models describing public and partner (tech) endpoints.
- Built-in pagination helpers (`paginate`, `paginate_async`).
- Support for rate limiting and retries through dedicated helpers.
- Optional FastAPI/uvicorn webhook listener with authorization checks.

Installation
------------

Install the base package in editable mode (recommended for development):

```bash
pip install -e .
```

Extras:

- `webhooks` – installs FastAPI and uvicorn for the embedded listener.
- `dev` – installs pytest and tools used by the test suite.

```bash
pip install -e '.[webhooks]'
pip install -e '.[dev]'
```

Python 3.9 or newer is required.

Quick Start
-----------

```python
import asyncio
from wazzup_client.client import WazzupClient


async def main() -> None:
    async with WazzupClient(api_key="your-client-api-key") as client:
        # Create an account contact
        await client.contacts.create(
            contact_id="crm-contact-1",
            responsible_user_id="crm-user-1",
            name="Alice",
            contact_data=[{"chatType": "telegram", "chatId": "alice_tg"}],
        )

        # Fetch contact information
        contact = await client.contacts.get("crm-contact-1")
        print(contact.name)

        # Assign a manager to a channel
        await client.channels.assign_user("crm-user-1", "channel-guid", role="manager")

        # List deals using typed Pydantic models
        deals = await client.deals.list(offset=0)
        for deal in deals:
            print(deal.id, deal.name)


if __name__ == "__main__":
    asyncio.run(main())
```

Architecture and Legacy Compatibility
-------------------------------------

The modern `WazzupClient` is a thin facade over `WazzupLegacyClient`. Each namespace (contacts, users, etc.) wraps the corresponding legacy methods (`list_contacts`, `create_user`, and so on) and converts responses to Pydantic models where possible.

Key benefits:

- Existing integrations relying on the legacy method names continue to work because no transport logic was removed.
- New integrations receive rich type information and consistent method naming (`client.<resource>.<action>`).
- The facade exposes convenience utilities (webhooks, pagination, retry helpers) without breaking the legacy API surface.

Resource Namespaces
-------------------

Each namespace is exposed as a `TypedResource` instance with standard CRUD operations:

| Namespace         | Legacy method prefixes                                           |
|-------------------|------------------------------------------------------------------|
| `client.contacts` | `list_contacts`, `get_contact`, `create_contact`, `delete_contact` |
| `client.users`    | `list_users`, `get_user`, `create_user`, `delete_user`             |
| `client.deals`    | `list_deals`, `get_deal`, `create_deal`, `delete_deal`             |
| `client.channels` | `assign_user_to_channel`, `assign_users_to_channel`, `remove_user_from_channel` |
| `client.pipelines`| `list_pipelines`, `get_pipeline`, `create_pipeline`, `delete_pipeline` (where available) |
| `client.accounts` | `get_account_settings`, `update_account_settings`, `get_balance`   |
| `client.webhooks` | `get_webhook_settings`, `update_webhook_settings`, `test_webhook`, listener helpers |

Extending with a new resource typically requires adding one line to `WazzupClient.__init__` and ensuring the legacy client implements the underlying methods.

Working with Responses
----------------------

- `list()` returns a `ResourceList[T]` holding typed Pydantic models and the untouched legacy payload (`resource_list.raw`). Iterate over the list or inspect `raw` for metadata such as offsets.
- `get()`, `create()`, and `update()` return Pydantic models when the legacy payload can be validated. If validation fails, the raw dictionary is returned to avoid hiding data.
- `delete()` always returns a dictionary (often empty) mirroring the legacy behaviour.

Async Usage Patterns
--------------------

The client supports both context manager and manual lifecycle management:

```python
client = WazzupClient(api_key="...")
try:
    users = await client.users.list()
finally:
    await client.close()
```

For repeated requests within the same event loop prefer the async context manager (`async with`) to ensure the underlying HTTP clients are closed cleanly.

Configuration Helpers
---------------------

- Pagination: `paginate` / `paginate_async` generators live in `wazzup_client.pagination`.
- Retries: configure `wazzup_client.retry.RetryOptions` for legacy clients that honour retry settings.
- Rate limiting: `wazzup_client.rate_limiter.RateLimiter` integrates with the base client to throttle specific buckets (e.g., `"messages"`).

Testing
-------

Install dependencies:

```bash
pip install -e '.[dev,webhooks]'
```

Run the suite:

```bash
pytest
```

The tests cover:

- Facade behaviour (`tests/test_client_facade.py`).
- Webhook routing and authorization (`tests/test_webhook_events.py`).
- Additional integration tests can be added under `tests/integration` and marked with `@pytest.mark.integration`.

Project Structure
-----------------

```
wazzup_client/
    client.py            # Modern facade and namespaces
    legacy_client.py     # Existing legacy implementation (async)
    public/              # Public API client, endpoints, and schemas
    tech/                # Partner/tech API client and schemas
    pagination.py        # Helper utilities for paging
    rate_limiter.py      # Simple token-bucket implementation
    retry.py             # Retry options used by the base client
tests/
    test_client_facade.py
    test_webhook_events.py
examples/
    client_usage.py
    partners_usage.py
```

Contributing
------------

1. Fork and clone the repository.
2. Install dependencies: `pip install -e '.[dev,webhooks]'`.
3. Run linting/formatting if applicable (e.g., `ruff`, `black`) and ensure `pytest` passes.
4. Submit a pull request describing the change and any additional tests.

Webhook Listener
----------------

The SDK includes a FastAPI-based webhook listener that can be started from `client.webhooks`. This is optional and mostly intended for local development or lightweight deployments.

### Starting the listener

```python
import asyncio

from wazzup_client.client import WazzupClient
from wazzup_client.public.schemas import MessagesWebhook


async def bootstrap_webhooks():
    async with WazzupClient(api_key="client-key", crm_key="crm-key") as client:
        listener_url = await client.webhooks.start_listener(
            host="0.0.0.0",
            port=8080,
            path="/webhooks",
        )

        # Update Wazzup with the listener settings
        await client.webhooks.ensure(
            uri=listener_url,
            auth_token="crm-key",
            subscriptions={"messagesAndStatuses": True},
        )

        @client.webhooks.on(MessagesWebhook)
        async def handle_messages(event: MessagesWebhook) -> None:
            for message in event.messages:
                print(f"{message.channelId}: {message.text}")

        # Keep the listener running until cancelled
        await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(bootstrap_webhooks())
```

- Passing `crm_key` to `WazzupClient` automatically enforces the expected `Authorization: Bearer` header for inbound webhooks.
- `start_listener(require_bearer="...")` can override the stored token at runtime.
- Use `client.webhooks.ensure()` to configure the webhook URI and subscriptions on the Wazzup API.
- For manual testing, the router exposes `dispatch()` so you can trigger handlers with sample payloads without starting FastAPI.

License
-------

MIT License. See `LICENSE` for details.
