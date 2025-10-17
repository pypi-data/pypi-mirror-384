Wazzup Python SDK
=================

An asynchronous, developer-friendly Python client for the Wazzup public and tech APIs. The package modernises the legacy client by offering typed namespaces, predictable CRUD-style methods, and optional webhook handling utilities.

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [WazzupClient](#wazzupclient)
- [Resource Classes](#resource-classes)
  - [BaseResource](#baseresource)
  - [TypedResource](#typedresource)
  - [ChannelsResource](#channelsresource)
  - [UsersResource](#usersresource)
  - [AccountsResource](#accountsresource)
- [WebhooksNamespace](#webhooksnamespace)
- [Data Models](#data-models)
- [Context Manager](#context-manager)
- [Configuration Helpers](#configuration-helpers)
- [Webhook Listener](#webhook-listener)
- [Examples](#examples)

## Overview

An asynchronous, developer-friendly Python client for the Wazzup public and tech APIs. The package modernises the legacy client by offering typed namespaces, predictable CRUD-style methods, and optional webhook handling utilities.

### Features

- Async-first API built on `httpx`
- Typed accessors for key resources (`contacts`, `users`, `deals`, `channels`, `pipelines`, `accounts`, `webhooks`)
- Automatic fallback to legacy methods to preserve backwards compatibility
- Pydantic models describing public and partner (tech) endpoints
- Built-in pagination helpers (`paginate`, `paginate_async`)
- Support for rate limiting and retries through dedicated helpers
- Optional FastAPI/uvicorn webhook listener with authorization checks
- Async context manager helper `wazzup_client_context` for safe reuse in background tasks

## Installation

Install the package from PyPI:

```bash
pip install wazzup-pysdk
```

For development, install in editable mode:

```bash
pip install -e .
```

Extras:

- `webhooks` – installs FastAPI and uvicorn for the embedded listener

```bash
pip install wazzup-pysdk[webhooks]
# or for development
pip install -e '.[webhooks]'
```

Python 3.9 or newer is required.

## WazzupClient

The main facade class that provides organized access to the Wazzup API through typed resource namespaces.

### Constructor

```python
WazzupClient(
    api_key: str,
    tech_base_url: str = "https://tech.wazzup24.com",
    public_base_url: str = "https://api.wazzup24.com",
    *,
    timeout: Optional[float] = None,
    crm_key: Optional[str] = None,
)
```

**Parameters:**
- `api_key` (str): Your Wazzup API key
- `tech_base_url` (str): Base URL for technical API endpoints
- `public_base_url` (str): Base URL for public API endpoints  
- `timeout` (Optional[float]): Request timeout in seconds
- `crm_key` (Optional[str]): CRM key for webhook authentication

### Properties

- `contacts`: TypedResource[Contact] - Contact management
- `users`: UsersResource - User management with additional helpers
- `deals`: TypedResource[Deal] - Deal management
- `pipelines`: TypedResource[Pipeline] - Pipeline management
- `accounts`: AccountsResource - Account operations
- `channels`: ChannelsResource - Channel management with specialized methods
- `webhooks`: WebhooksNamespace - Webhook configuration and event handling

### Resource Namespaces

Each namespace is exposed as a `TypedResource` instance with standard CRUD operations:

| Namespace         | Available Methods                                           |
|-------------------|-------------------------------------------------------------|
| `client.contacts` | `list`, `get`, `create`, `update`, `delete` |
| `client.users`    | `list`, `get`, `create`, `update`, `delete`, `list_raw`, `get_raw`, `create_many` (bulk) |
| `client.deals`    | `list`, `get`, `create`, `update`, `delete`             |
| `client.channels` | `list`, `get`, `create`, `update`, `delete`, `info`, `reinitialize`, `generate_link`, `assign_user`, `assign_users`, `remove_user`, `normalized` |
| `client.pipelines`| `list`, `get`, `create`, `update`, `delete` (where available) |
| `client.accounts` | `create`, `get_settings`, `update_settings`, `balance`, `user_roles` |
| `client.webhooks` | `settings`, `update`, `ensure`, `test`, `start_listener`, `stop_listener`, `on` decorator |

### Methods

#### `async close() -> None`
Release underlying client resources and stop webhook listeners.

#### `async __aenter__() -> WazzupClient`
Async context manager entry.

#### `async __aexit__(*exc: Any) -> None`
Async context manager exit.

#### `__repr__() -> str`
String representation showing API key (masked) and available namespaces.

## Resource Classes

### BaseResource

Generic CRUD wrapper providing a namespace per API resource.

#### Methods

##### `async list(**params: Any) -> Union[ResourceList[ModelT], Any]`
List all items of this resource.

**Parameters:**
- `**params`: Query parameters to pass to the API

**Returns:**
- `ResourceList[ModelT]` if model is configured, otherwise raw API response

##### `async get(id: str) -> Union[ModelT, Any]`
Fetch a single resource by identifier.

**Parameters:**
- `id` (str): Resource identifier

**Returns:**
- `ModelT` if model is configured, otherwise raw API response

##### `async create(**data: Any) -> Union[ModelT, Dict[str, Any]]`
Create a new resource instance.

**Parameters:**
- `**data`: Resource data to create

**Returns:**
- `ModelT` if model is configured and validation succeeds, otherwise raw response

##### `async update(id: str, **data: Any) -> Union[ModelT, Dict[str, Any]]`
Update an existing resource instance.

**Parameters:**
- `id` (str): Resource identifier
- `**data`: Updated resource data

**Returns:**
- `ModelT` if model is configured and validation succeeds, otherwise raw response

##### `async delete(id: str) -> Dict[str, Any]`
Delete a resource by identifier.

**Parameters:**
- `id` (str): Resource identifier

**Returns:**
- Dictionary with deletion result

### TypedResource

Typed resource that guarantees Pydantic objects for common operations.

#### Methods

##### `async list(**params: Any) -> ResourceList[ModelT]`
List all items with guaranteed typed results.

##### `async get(id: str) -> ModelT`
Fetch a single resource with guaranteed typed result.

##### `async create(**data: Any) -> Union[ModelT, Dict[str, Any]]`
Create a new resource instance.

##### `async update(id: str, **data: Any) -> Union[ModelT, Dict[str, Any]]`
Update an existing resource instance.

### ChannelsResource

Additional channel-specific helpers that wrap legacy calls.

#### Methods

##### `async list(**_params: Any) -> ResourceList[ChannelItem]`
List channels and expose normalized payload via `.raw`.

**Returns:**
- `ResourceList[ChannelItem]` with normalized raw data

##### `async normalized() -> Dict[str, Any]`
Return channels in the historical dict format.

**Returns:**
- Dictionary with channels and count

##### `async info(transport: str, channel_id: str) -> Dict[str, Any]`
Fetch detailed information for a channel.

**Parameters:**
- `transport` (str): Transport type (whatsapp, telegram, etc.)
- `channel_id` (str): Channel identifier

##### `async create(*, transport: str, **data: Any) -> Dict[str, Any]`
Create a channel.

**Parameters:**
- `transport` (str): Transport type
- `**data`: Channel creation data

##### `async reinitialize(transport: str, channel_id: str) -> Dict[str, Any]`
Reinitialize a channel session.

**Parameters:**
- `transport` (str): Transport type
- `channel_id` (str): Channel identifier

##### `async delete(*, transport: str, channel_id: str, delete_chats: bool = True) -> Dict[str, Any]`
Delete a channel.

**Parameters:**
- `transport` (str): Transport type
- `channel_id` (str): Channel identifier
- `delete_chats` (bool): Whether to delete associated chats

##### `async generate_link(payload: Mapping[str, Any]) -> Dict[str, Any]`
Generate a channel connection link payload.

**Parameters:**
- `payload` (Mapping[str, Any]): Link generation parameters

##### `async assign_user(user_id: str, channel_id: str, role: str = "seller", allow_get_new_clients: bool = True) -> Any`
Assign a single user to a channel with an optional role.

**Parameters:**
- `user_id` (str): User identifier
- `channel_id` (str): Channel identifier
- `role` (str): User role in channel
- `allow_get_new_clients` (bool): Whether user can receive new clients

##### `async assign_users(user_assignments: List[Dict[str, Any]], channel_id: str) -> Any`
Assign multiple users to a channel.

**Parameters:**
- `user_assignments` (List[Dict[str, Any]]): List of user assignment data
- `channel_id` (str): Channel identifier

##### `async remove_user(user_id: str, channel_id: str) -> Any`
Remove a user from a channel.

**Parameters:**
- `user_id` (str): User identifier
- `channel_id` (str): Channel identifier

### UsersResource

Typed user resource with raw helpers.

#### Methods

##### `async list_raw() -> List[Dict[str, Any]]`
Return the raw users payload.

##### `async get_raw(user_id: str) -> Dict[str, Any]`
Fetch raw user data by identifier.

**Parameters:**
- `user_id` (str): User identifier

##### `async create_many(users: Sequence[Mapping[str, Any]]) -> Dict[str, Any]`
Bulk create or update users.

**Parameters:**
- `users` (Sequence[Mapping[str, Any]]): List of user data

### AccountsResource

Account operations with dedicated helpers.

#### Methods

##### `async create(*, name: str, lang: str = "ru", currency: str = "RUB", crm_key: Optional[str] = None) -> Dict[str, Any]`
Create a new account.

**Parameters:**
- `name` (str): Account name
- `lang` (str): Language code
- `currency` (str): Currency code
- `crm_key` (Optional[str]): CRM integration key

##### `async get_settings() -> Dict[str, Any]`
Fetch account settings.

##### `async settings() -> Dict[str, Any]`
Backward compatible alias for get_settings.

##### `async update_settings(**params: Any) -> Dict[str, Any]`
Update account settings.

**Parameters:**
- `**params`: Settings to update

##### `async balance() -> Dict[str, Any]`
Get account balance.

##### `async get_balance() -> Dict[str, Any]`
Backward compatible alias for balance.

##### `async user_roles(user_id: str) -> List[Dict[str, Any]]`
Return user roles across channels.

**Parameters:**
- `user_id` (str): User identifier

## WebhooksNamespace

Manage webhook API settings and expose a local webhook listener.

### Constructor

```python
WebhooksNamespace(expected_bearer: Optional[str] = None)
```

### Properties

- `events`: WebhookEventRouter - Event router for handling webhooks
- `url`: str - Current webhook listener URL

### Methods

##### `async settings() -> WebhooksSettings`
Get current webhook settings.

##### `async update(settings: Union[WebhooksSettings, Mapping[str, Any]]) -> WebhooksSettings`
Update webhook settings.

**Parameters:**
- `settings`: Webhook settings as model or dictionary

##### `async ensure(*, uri: str, auth_token: Optional[str] = None, subscriptions: Union[WebhookSubscriptions, Mapping[str, Any], None] = None) -> WebhooksSettings`
Ensure webhook settings are configured.

**Parameters:**
- `uri` (str): Webhook endpoint URI
- `auth_token` (Optional[str]): Authentication token
- `subscriptions` (Optional): Event subscriptions

##### `async test(uri: str) -> Dict[str, Any]`
Test webhook endpoint.

**Parameters:**
- `uri` (str): Webhook URI to test

##### `async start_listener(*, host: str = "0.0.0.0", port: int = 8080, path: str = "/webhooks", log_level: str = "warning", require_bearer: Optional[str] = None) -> str`
Start local webhook listener.

**Parameters:**
- `host` (str): Listen host
- `port` (int): Listen port
- `path` (str): Webhook path
- `log_level` (str): Logging level
- `require_bearer` (Optional[str]): Required bearer token

**Returns:**
- Listener URL

##### `async stop_listener() -> None`
Stop webhook listener.

##### `on(event: Union[str, Type[BaseModel]]) -> Callable[[Handler], Handler]`
Decorator to register webhook event handlers.

**Parameters:**
- `event`: Event name or Pydantic model class

**Returns:**
- Decorator function

##### `expect_bearer(token: Optional[str]) -> None`
Set expected bearer token for webhook authentication.

**Parameters:**
- `token` (Optional[str]): Bearer token

##### `async close() -> None`
Close webhook namespace and stop listeners.

## Data Models

### Core Models

#### User
```python
class User(BaseModel):
    id: str  # Max 64 characters
    name: str  # Max 150 characters
    phone: Optional[str] = None  # 8-15 digits
```

#### Contact
```python
class Contact(BaseModel):
    id: str  # Max 100 characters
    name: str  # Max 200 characters
    data: List[ContactData]
    uri: Optional[str] = None  # Max 200 characters
```

#### ContactData
```python
class ContactData(BaseModel):
    chatType: str  # whatsapp, whatsgroup, viber, instagram, telegram, telegroup, vk, avito, max, maxgroup
    chatId: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None  # 8-15 digits, only for telegram/max
```

#### Deal
```python
class Deal(BaseModel):
    id: str  # Max 100 characters
    responsibleUserId: str  # Max 100 characters
    name: str  # Max 200 characters
    contacts: List[str]  # 1-10 contact IDs
    uri: str  # Max 200 characters
    closed: Optional[bool] = None
```

#### Pipeline
```python
class Pipeline(BaseModel):
    id: str  # Max 100 characters
    name: str  # Max 200 characters
    stages: List[PipelineStage]
    uri: str  # Max 200 characters
```

#### PipelineStage
```python
class PipelineStage(BaseModel):
    id: str  # Max 100 characters
    name: str  # Max 100 characters
    order: int
    color: Optional[str] = None
    uri: str  # Max 200 characters
```

#### ChannelItem
```python
class ChannelItem(BaseModel):
    id: str
    name: str
    transport: str
    status: str
    # Additional fields vary by transport
```

### Webhook Models

#### WebhooksSettings
```python
class WebhooksSettings(BaseModel):
    webhooksUri: Optional[str] = None
    webhooksAuthToken: Optional[str] = None
    subscriptions: Optional[WebhookSubscriptions] = None
```

#### WebhookSubscriptions
```python
class WebhookSubscriptions(BaseModel):
    messages: Optional[bool] = None
    statuses: Optional[bool] = None
    createEntities: Optional[bool] = None
    channelsUpdates: Optional[bool] = None
    templateStatus: Optional[bool] = None
```

#### MessagesWebhook
```python
class MessagesWebhook(BaseModel):
    messages: List[WebhookMessageItem]
```

#### StatusesWebhook
```python
class StatusesWebhook(BaseModel):
    statuses: List[StatusItem]
```

#### CreateEntitiesWebhook
```python
class CreateEntitiesWebhook(BaseModel):
    createContact: Optional[CreateContactPayload] = None
    createDeal: Optional[CreateDealPayload] = None
```

### Message Models

#### MessageSendRequest
```python
class MessageSendRequest(BaseModel):
    channelId: str
    chatType: str  # whatsapp, whatsgroup, viber, instagram, telegram, telegroup, vk, avito, max, maxgroup
    chatId: Optional[str] = None
    text: Optional[str] = None
    contentUri: Optional[AnyUrl] = None
    refMessageId: Optional[str] = None
    crmUserId: Optional[str] = None
    crmMessageId: Optional[str] = None
    username: Optional[str] = None
    phone: Optional[str] = None  # 8-15 digits
    clearUnanswered: Optional[bool] = None
    templateId: Optional[str] = None
    templateValues: Optional[List[str]] = None
    buttonsObject: Optional[ButtonsObject] = None
```

#### MessageSendResponse
```python
class MessageSendResponse(BaseModel):
    messageId: str
    chatId: Optional[str] = None
    # Additional response fields
```

## Context Manager

### wazzup_client_context

Async context manager that yields a WazzupClient and closes it automatically.

```python
async def wazzup_client_context(
    api_key: str,
    *,
    tech_base_url: str = "https://tech.wazzup24.com",
    public_base_url: str = "https://api.wazzup24.com",
    timeout: Optional[float] = None,
    crm_key: Optional[str] = None,
) -> AsyncIterator[WazzupClient]:
```

**Parameters:**
- `api_key` (str): Your Wazzup API key
- `tech_base_url` (str): Base URL for technical API endpoints
- `public_base_url` (str): Base URL for public API endpoints
- `timeout` (Optional[float]): Request timeout in seconds
- `crm_key` (Optional[str]): CRM key for webhook authentication

## Examples

### Basic Usage

```python
import asyncio
from wazzup_client.client import WazzupClient

async def main():
    client = WazzupClient(api_key="your_api_key")
    
    # List contacts
    contacts = await client.contacts.list()
    for contact in contacts:
        print(f"Contact: {contact.name}")
    
    # Create a new contact
    new_contact = await client.contacts.create(
        name="John Doe",
        data=[{
            "chatType": "whatsapp",
            "chatId": "1234567890"
        }]
    )
    
    await client.close()

asyncio.run(main())
```

### Using Context Manager

```python
import asyncio
from wazzup_client.client import wazzup_client_context

async def main():
    async with wazzup_client_context(api_key="your_api_key") as client:
        # List users
        users = await client.users.list()
        print(f"Found {len(users)} users")
        
        # Get account balance
        balance = await client.accounts.balance()
        print(f"Account balance: {balance}")

asyncio.run(main())
```

### Webhook Handling

```python
import asyncio
from wazzup_client.client import WazzupClient
from wazzup_client.public.schemas import MessagesWebhook

async def main():
    client = WazzupClient(api_key="your_api_key", crm_key="your_crm_key")
    
    # Register webhook handlers
    @client.webhooks.on("messages")
    async def handle_messages(payload: dict):
        print(f"Received message: {payload}")
    
    @client.webhooks.on(MessagesWebhook)
    async def handle_typed_messages(webhook: MessagesWebhook):
        for message in webhook.messages:
            print(f"Message from {message.senderName}: {message.text}")
    
    # Start webhook listener
    url = await client.webhooks.start_listener(port=8080)
    print(f"Webhook listener started at {url}")
    
    # Configure webhooks
    await client.webhooks.ensure(
        uri=url,
        auth_token="your_crm_key",
        subscriptions={
            "messages": True,
            "statuses": True
        }
    )
    
    # Keep running
    try:
        await asyncio.sleep(3600)  # Run for 1 hour
    finally:
        await client.close()

asyncio.run(main())
```

### Channel Management

```python
import asyncio
from wazzup_client.client import WazzupClient

async def main():
    client = WazzupClient(api_key="your_api_key")
    
    # List channels
    channels = await client.channels.list()
    print(f"Found {len(channels)} channels")
    
    # Get channel info
    channel_info = await client.channels.info("whatsapp", "channel_id")
    print(f"Channel info: {channel_info}")
    
    # Assign user to channel
    await client.channels.assign_user(
        user_id="user_id",
        channel_id="channel_id",
        role="seller"
    )
    
    await client.close()

asyncio.run(main())
```

### Bulk Operations

```python
import asyncio
from wazzup_client.client import WazzupClient

async def main():
    client = WazzupClient(api_key="your_api_key")
    
    # Bulk create users
    users_data = [
        {"id": "user1", "name": "User One", "phone": "1234567890"},
        {"id": "user2", "name": "User Two", "phone": "0987654321"}
    ]
    
    result = await client.users.create_many(users_data)
    print(f"Created users: {result}")
    
    # Bulk assign users to channel
    assignments = [
        {"userId": "user1", "role": "seller"},
        {"userId": "user2", "role": "manager"}
    ]
    
    await client.channels.assign_users(assignments, "channel_id")
    
    await client.close()

asyncio.run(main())
```

## Webhook Listener

The SDK includes a FastAPI-based webhook listener that can be started from `client.webhooks`. This is optional and mostly intended for local development or lightweight deployments.

### Typed payload parsing without the router

If you already have an HTTP endpoint, use `parse_webhook_payload` for lightweight, typed dispatch:

```python
from typing import Any, Mapping

from wazzup_client.public.schemas import ChannelsUpdatesWebhook, MessagesWebhook
from wazzup_client.webhook_events import parse_webhook_payload


async def handle_wazzup_webhook(payload: Mapping[str, Any]) -> None:
    parsed = parse_webhook_payload(payload)

    if parsed.name == "messages":
        event = parsed.require_model(MessagesWebhook)
        for message in event.messages:
            print(f"[{message.channelId}] {message.text}")
    elif parsed.name == "channelsUpdates":
        updates = parsed.require_model(ChannelsUpdatesWebhook)
        print(f"{len(updates.channelsUpdates)} channels updated")
    else:
        # Unknown webhook payload – fall back to raw dict
        print(parsed.payload)
```

Combine this with your own bearer validation logic or reuse `client.webhooks.expect_bearer(token)` to align with CRM secrets.

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

**Key points:**
- Passing `crm_key` to `WazzupClient` automatically enforces the expected `Authorization: Bearer` header for inbound webhooks
- `start_listener(require_bearer="...")` can override the stored token at runtime
- Use `client.webhooks.ensure()` to configure the webhook URI and subscriptions on the Wazzup API
- For manual testing, the router exposes `dispatch()` so you can trigger handlers with sample payloads without starting FastAPI


License
-------

MIT License. See `LICENSE` for details.
