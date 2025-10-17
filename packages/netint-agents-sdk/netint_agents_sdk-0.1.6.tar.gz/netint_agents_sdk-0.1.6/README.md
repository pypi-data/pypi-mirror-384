# NetInt Agents SDK

A Python SDK for interacting with the NetIntGPT Agents API.

## Installation

```bash
pip install -e .
```

## Quick Start

```python
from netint_agents_sdk import NetIntClient

client = NetIntClient.from_env()
environments = client.environments.list()
print(f"Found {len(environments)} environments")
```

## Documentation

See `QUICKSTART.md` and `docs/USAGE_GUIDE.md` for detailed documentation.
