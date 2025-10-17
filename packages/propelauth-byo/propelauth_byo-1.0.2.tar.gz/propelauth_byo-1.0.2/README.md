# PropelAuth BYO Python Client

Python client library for PropelAuth BYO (Bring Your Own) authentication service.

## Installation

```bash
pip install propelauth-byo
```

## Usage

```python
from propelauth_byo import create_client

client = create_client(
    url="https://your-byo-instance.com",
    integration_key="your-integration-key"
)

# Use the client for authentication operations
result = await client.ping()
```
