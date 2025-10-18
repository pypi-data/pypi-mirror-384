# Me

Types:

```python
from blooio.types import MeRetrieveResponse
```

Methods:

- <code title="get /v1/api/me">client.me.<a href="./src/blooio/resources/me.py">retrieve</a>() -> <a href="./src/blooio/types/me_retrieve_response.py">MeRetrieveResponse</a></code>

# Contacts

Types:

```python
from blooio.types import ContactCheckCapabilitiesResponse
```

Methods:

- <code title="get /v1/api/contacts/{contact}/capabilities">client.contacts.<a href="./src/blooio/resources/contacts.py">check_capabilities</a>(contact) -> <a href="./src/blooio/types/contact_check_capabilities_response.py">ContactCheckCapabilitiesResponse</a></code>

# Messages

Types:

```python
from blooio.types import (
    MessageRetrieveResponse,
    MessageCancelResponse,
    MessageGetStatusResponse,
    MessageSendResponse,
)
```

Methods:

- <code title="get /v1/api/messages/{messageId}">client.messages.<a href="./src/blooio/resources/messages.py">retrieve</a>(message_id) -> <a href="./src/blooio/types/message_retrieve_response.py">MessageRetrieveResponse</a></code>
- <code title="delete /v1/api/messages/{messageId}">client.messages.<a href="./src/blooio/resources/messages.py">cancel</a>(message_id) -> <a href="./src/blooio/types/message_cancel_response.py">MessageCancelResponse</a></code>
- <code title="get /v1/api/messages/{messageId}/status">client.messages.<a href="./src/blooio/resources/messages.py">get_status</a>(message_id) -> <a href="./src/blooio/types/message_get_status_response.py">MessageGetStatusResponse</a></code>
- <code title="post /v1/api/messages">client.messages.<a href="./src/blooio/resources/messages.py">send</a>(\*\*<a href="src/blooio/types/message_send_params.py">params</a>) -> <a href="./src/blooio/types/message_send_response.py">MessageSendResponse</a></code>

# Config

## Webhook

Types:

```python
from blooio.types.config import WebhookRetrieveResponse, WebhookUpdateResponse
```

Methods:

- <code title="get /v1/api/config/webhook">client.config.webhook.<a href="./src/blooio/resources/config/webhook.py">retrieve</a>() -> <a href="./src/blooio/types/config/webhook_retrieve_response.py">WebhookRetrieveResponse</a></code>
- <code title="put /v1/api/config/webhook">client.config.webhook.<a href="./src/blooio/resources/config/webhook.py">update</a>(\*\*<a href="src/blooio/types/config/webhook_update_params.py">params</a>) -> <a href="./src/blooio/types/config/webhook_update_response.py">WebhookUpdateResponse</a></code>

# Batches

Methods:

- <code title="post /v1/api/batches">client.batches.<a href="./src/blooio/resources/batches.py">create</a>() -> None</code>
- <code title="get /v1/api/batches/{batchId}">client.batches.<a href="./src/blooio/resources/batches.py">retrieve</a>(batch_id) -> None</code>
- <code title="get /v1/api/batches/{batchId}/messages">client.batches.<a href="./src/blooio/resources/batches.py">list_messages</a>(batch_id) -> None</code>
- <code title="get /v1/api/batches/{batchId}/status">client.batches.<a href="./src/blooio/resources/batches.py">retrieve_status</a>(batch_id) -> None</code>
