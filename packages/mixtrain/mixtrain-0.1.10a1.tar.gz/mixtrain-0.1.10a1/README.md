# Mixtrain

**Mixtrain** is a Python SDK and CLI for [mixtrain.ai](https://mixtrain.ai) platform.

## Installation

Using uv
```bash
uv add mixtrain
```
or if you use pip

```bash
pip install mixtrain
```

To install mixtrain CLI globally, using uv

```bash
uv tool install mixtrain
```
or if you use pipx

```bash
pipx mixtrain
```

## Quick Start

### Authentication

#### Option 1: Interactive Login (Development)

```bash
mixtrain login
```

#### Option 2: API Key (Production/Automation)

For production deployments, CI/CD, or automated scripts, use API key authentication:

```bash
# Set your API key as an environment variable
export MIXTRAIN_API_KEY=mix-your-api-key-here

# Now you can use mixtrain without login
mixtrain workspace list
```

Or in Python:

```python
import os
os.environ['MIXTRAIN_API_KEY'] = 'mix-your-api-key-here'

from mixtrain import MixClient
client = MixClient()
configs = client.list_routing_configs()
```

Get your API key from the [mixtrain.ai dashboard](https://app.mixtrain.ai).

### CLI Usage

Refer to `mixtrain --help` for the full list of commands.

### Python SDK

Refer to https://mixtrain.ai for more details.