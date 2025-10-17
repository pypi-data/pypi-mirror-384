# Vyre Python SDK

A Python client for the Vyre AI chat API.

## Installation

```bash
pip install vyre-sdk
```

## Quick Start

```python
from vyre import Vyre

# Initialize client
vyre = Vyre(api_key='your-api-key')

# Send a message
response = vyre.chat(message="Hello, world!")
print(response['reply'])

# Continue conversation
follow_up = vyre.chat(
    message="Tell me more",
    chat_id=response['chat_id']
)
```

## Async Support

```python
import asyncio
from vyre import AsyncVyre

async def main():
    vyre = AsyncVyre(api_key='your-api-key')
    response = await vyre.chat(message="Hello async world!")
    print(response['reply'])

asyncio.run(main())
```

## Features

- Synchronous and asynchronous API support
- Automatic error handling and retries
- File upload capabilities
- Webhook management
- Conversation management
- Type hints for better IDE support

## Documentation

Full documentation is available at [docs.vyre.com](https://docs.vyre.com)

## License

MIT License
