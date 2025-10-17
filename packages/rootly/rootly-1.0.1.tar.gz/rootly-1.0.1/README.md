# Rootly Python SDK

A Python client library for accessing the [Rootly API v1](https://rootly.com/). This SDK provides both synchronous and asynchronous interfaces for interacting with Rootly's incident management platform.

[![PyPI version](https://badge.fury.io/py/rootly.svg)](https://badge.fury.io/py/rootly)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

## Installation

```bash
pip install rootly
```

## Quick Start

### Basic Usage

First, create a client:

```python
from rootly_sdk import Client

client = Client(base_url="https://api.rootly.com")
```

### Authentication

For endpoints that require authentication, use `AuthenticatedClient`:

```python
from rootly_sdk import AuthenticatedClient

client = AuthenticatedClient(
    base_url="https://api.rootly.com",
    token="your-api-token"
)
```

### Making API Calls

```python
from rootly_sdk.models import MyDataModel
from rootly_sdk.api.my_tag import get_my_data_model
from rootly_sdk.types import Response

# Simple synchronous call
with client as client:
    my_data: MyDataModel = get_my_data_model.sync(client=client)

    # Or get detailed response (includes status_code, headers, etc.)
    response: Response[MyDataModel] = get_my_data_model.sync_detailed(client=client)
```

### Async Usage

```python
from rootly_sdk.models import MyDataModel
from rootly_sdk.api.my_tag import get_my_data_model
from rootly_sdk.types import Response

async with client as client:
    my_data: MyDataModel = await get_my_data_model.asyncio(client=client)
    response: Response[MyDataModel] = await get_my_data_model.asyncio_detailed(client=client)
```

## Advanced Configuration

### SSL Certificate Verification

By default, the client verifies SSL certificates. For internal APIs with custom certificates:

```python
client = AuthenticatedClient(
    base_url="https://internal-api.example.com",
    token="your-api-token",
    verify_ssl="/path/to/certificate_bundle.pem",
)
```

**Warning:** Disabling SSL verification is a security risk and should only be used in development:

```python
client = AuthenticatedClient(
    base_url="https://internal-api.example.com",
    token="your-api-token",
    verify_ssl=False
)
```

### Custom HTTP Client Configuration

You can customize the underlying `httpx.Client` with event hooks and other options:

```python
from rootly_sdk import Client

def log_request(request):
    print(f"Request: {request.method} {request.url}")

def log_response(response):
    print(f"Response: {response.request.method} {response.request.url} - Status {response.status_code}")

client = Client(
    base_url="https://api.rootly.com",
    httpx_args={
        "event_hooks": {
            "request": [log_request],
            "response": [log_response]
        }
    },
)
```

Access the underlying httpx client directly:

```python
# Synchronous client
httpx_client = client.get_httpx_client()

# Asynchronous client
async_httpx_client = client.get_async_httpx_client()
```

Set a custom httpx client (note: this overrides base_url and other settings):

```python
import httpx
from rootly_sdk import Client

client = Client(base_url="https://api.rootly.com")
client.set_httpx_client(
    httpx.Client(
        base_url="https://api.rootly.com",
        proxies="http://localhost:8030"
    )
)
```

## API Structure

The SDK is structured as follows:

1. **Four function variants per endpoint:**
   - `sync`: Blocking request returning parsed data or `None`
   - `sync_detailed`: Blocking request returning full `Response` object
   - `asyncio`: Async version of `sync`
   - `asyncio_detailed`: Async version of `sync_detailed`

2. **Module organization:**
   - Path/query parameters and request bodies become function arguments
   - Endpoints are grouped by their first OpenAPI tag (e.g., `rootly_sdk.api.incidents`)
   - Untagged endpoints are in `rootly_sdk.api.default`

## Development

### Requirements

- Python 3.9 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation for Development

```bash
# Clone the repository
git clone https://github.com/rootlyhq/rootly-python.git
cd rootly-python

# Install in editable mode
pip install -e .
```

### Regenerating the Client

To regenerate the client from the latest OpenAPI specification:

```bash
openapi-python-client generate \
  --url https://rootly-heroku.s3.amazonaws.com/swagger/v1/swagger.json \
  --no-fail-on-warning \
  --output-path . \
  --overwrite \
  --config tools/config.yaml
```

### Building the Package

```bash
# Install build tools
pip install uv
uv pip install build

# Build distribution files
python -m build
```

### Running Tests

```bash
# Verify SDK imports successfully
python -c "import rootly_sdk; print('SDK imports successfully')"
```

## Publishing

### Automated Publishing via GitHub Actions (Recommended)

1. Update the version in `pyproject.toml`
2. Update `CHANGELOG.md` with release notes
3. Create and push a git tag:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```
4. GitHub Actions will automatically build and publish to PyPI

See [.github/PUBLISHING.md](.github/PUBLISHING.md) for detailed publishing instructions.

### Manual Publishing

If you need to publish manually:

```bash
# Install dependencies
pip install uv
uv pip install build twine

# Build the package
python -m build

# Publish to PyPI
twine upload dist/*
```

## Dependencies

- [httpx](https://www.python-httpx.org/) >= 0.20.0, < 0.29.0 - HTTP client
- [attrs](https://www.attrs.org/) >= 22.2.0 - Data classes
- [python-dateutil](https://dateutil.readthedocs.io/) >= 2.8.0 - Date parsing

## License

Apache 2.0

## Support

For issues, questions, or contributions, please visit the [GitHub repository](https://github.com/rootlyhq/rootly-python).
