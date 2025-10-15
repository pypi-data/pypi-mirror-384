# Veris AI Python SDK

[![PyPI version](https://badge.fury.io/py/veris-ai.svg)](https://badge.fury.io/py/veris-ai)
[![Python Versions](https://img.shields.io/pypi/pyversions/veris-ai.svg)](https://pypi.org/project/veris-ai/)
[![Downloads](https://static.pepy.tech/badge/veris-ai)](https://pepy.tech/project/veris-ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/veris-ai/veris-python-sdk/actions/workflows/test.yml/badge.svg)](https://github.com/veris-ai/veris-python-sdk/actions/workflows/test.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

For more information visit us at https://veris.ai

A Python package for Veris AI tools with simulation capabilities and FastAPI MCP (Model Context Protocol) integration.

## Quick Reference

**Purpose**: Tool mocking, tracing, and FastAPI MCP integration for AI agent development  
**Core Components**: [`tool_mock`](#function-mocking) • [`api_client`](src/veris_ai/api_client.py) • [`observability`](#sdk-observability-helpers) • [`agents_wrapper`](#openai-agents-integration) • [`fastapi_mcp`](#fastapi-mcp-integration) • [`jaeger_interface`](#jaeger-trace-interface)  
**Deep Dive**: [`Module Architecture`](src/veris_ai/README.md) • [`Testing Guide`](tests/README.md) • [`Usage Examples`](examples/README.md)  
**Source of Truth**: Implementation details in [`src/veris_ai/`](src/veris_ai/) source code

## Installation

```bash
# Base package
uv add veris-ai

# With optional extras
uv add "veris-ai[dev,fastapi,observability,agents]"
```

**Installation Profiles**:
- `dev`: Development tools (ruff, pytest, mypy) 
- `fastapi`: FastAPI MCP integration
- `observability`: OpenTelemetry tracing
- `agents`: OpenAI agents integration

## Import Patterns

**Semantic Tag**: `import-patterns`

```python
# Core imports (base dependencies only)
from veris_ai import veris, JaegerClient

# Optional features (require extras)
from veris_ai import init_observability, instrument_fastapi_app  # Requires observability extras
from veris_ai import Runner, VerisConfig  # Requires agents extras
```

**Complete Import Strategies**: See [`examples/README.md`](examples/README.md) for different import approaches, conditional features, and integration patterns.

## Configuration

**Semantic Tag**: `environment-config`

| Variable | Purpose | Default |
|----------|---------|---------|
| `VERIS_API_KEY` | API authentication key | None |
| `VERIS_MOCK_TIMEOUT` | Request timeout (seconds) | `90.0` |

**Advanced Configuration** (rarely needed):
- `VERIS_API_URL`: Override default API endpoint (defaults to production)

**Configuration Details**: See [`src/veris_ai/api_client.py`](src/veris_ai/api_client.py) for API configuration and [`src/veris_ai/tool_mock.py`](src/veris_ai/tool_mock.py) for environment handling logic.


### SDK Observability Helpers

The SDK provides optional-safe observability helpers that standardize OpenTelemetry setup and W3C context propagation across services.

```python
from fastapi import FastAPI
from veris_ai import init_observability, instrument_fastapi_app

# Initialize tracing/export early (no-op if dependencies are absent)
init_observability()

app = FastAPI()

# Ensure inbound HTTP requests continue W3C traces
instrument_fastapi_app(app)
```

#### Observability Environment

Set these environment variables to enable exporting traces via OTLP (Logfire) and ensure consistent service naming:

| Variable | Example | Notes |
|----------|---------|-------|
| `OTEL_SERVICE_NAME` | `simulation-server` | Should match `VERIS_SERVICE_NAME` used elsewhere to keep traces aligned |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `https://logfire-api.pydantic.dev` | OTLP HTTP endpoint |
| `LOGFIRE_TOKEN` | `FILL_IN` | Logfire API token used by the exporter |
| `OTEL_EXPORTER_OTLP_HEADERS` | `'Authorization=FILL_IN'` | Include quotes to preserve the `=`; often `Authorization=Bearer <LOGFIRE_TOKEN>` |

Quick setup example:

```bash
export OTEL_SERVICE_NAME="simulation-server"
export OTEL_EXPORTER_OTLP_ENDPOINT="https://logfire-api.pydantic.dev"
export LOGFIRE_TOKEN="<your-token>"
export OTEL_EXPORTER_OTLP_HEADERS="Authorization=${LOGFIRE_TOKEN}"
```

Then initialize in code early in your process:

```python
from veris_ai import init_observability, instrument_fastapi_app
init_observability()
app = FastAPI()
instrument_fastapi_app(app)
```

What this enables:
- Sets global W3C propagator (TraceContext + Baggage)
- Optionally instruments FastAPI, requests, httpx, MCP client if installed
- Includes request hooks to attach outbound `traceparent` on HTTP calls for continuity

End-to-end propagation with the simulator:
- The simulator injects W3C headers when connecting to your FastAPI MCP endpoints
- The SDK injects W3C headers on `/v3/tool_mock` and logging requests back to the simulator
- Result: customer agent spans and tool mocks appear under the same distributed trace

## Function Mocking

**Semantic Tag**: `tool-mocking`

### Session-Based Activation

The SDK uses session-based activation to determine when to enable mocking. Choose one of these methods to set a session ID:

**Option 1: Manual Setting**
```python
from veris_ai import veris

# Explicitly set a session ID
veris.set_session_id("your-session-id")

# Now decorated functions will use mock responses
result = await your_mocked_function()

# Clear session to disable mocking
veris.clear_session_id()
```

**Option 2: Automatic Extraction (FastAPI MCP)**
```python
# When using FastAPI MCP integration, session IDs are 
# automatically extracted from OAuth2 bearer tokens
veris.set_fastapi_mcp(...)
# No manual session management needed
```

**How it works internally**: Regardless of which method you use, session IDs are stored in Python context variables (`contextvars`). This ensures proper isolation between concurrent requests and automatic propagation through the call stack.

### Core Decorators

```python
from veris_ai import veris

# Mock decorator: Returns simulated responses when session ID is set
@veris.mock()
async def your_function(param1: str, param2: int) -> dict:
    """Function documentation for LLM context."""
    return {"result": "actual implementation"}

# Spy decorator: Executes function and logs calls/responses
@veris.spy()
async def monitored_function(data: str) -> dict:
    return process_data(data)

# Stub decorator: Returns fixed value in simulation
@veris.stub(return_value={"status": "success"})
async def get_data() -> dict:
    return await fetch_from_api()
```

**Behavior**: When a session ID is set, decorators activate their respective behaviors (mock responses, logging, or stubbed values). Without a session ID, functions execute normally.

**Implementation**: See [`src/veris_ai/tool_mock.py`](src/veris_ai/tool_mock.py) for decorator logic and API integration.

### Core Instrument

Instrument OpenAI agents without changing tool code by using the SDK's Runner (extends OpenAI's Runner) and an optional VerisConfig for fine control.

Requirements:
- Install extras: `uv add "veris-ai[agents]"`
- Set `ENV=simulation` to enable mock behavior (otherwise passes through)

Minimal usage:

```python
from veris_ai import Runner

result = await Runner.run(agent, "What's 10 + 5?")
```

Select tools to intercept (include/exclude):

```python
from veris_ai import Runner, VerisConfig

config = VerisConfig(include_tools=["calculator", "search_web"])  # or exclude_tools=[...]
result = await Runner.run(agent, "Process this", veris_config=config)
```

Per‑tool behavior via ToolCallOptions:

```python
from veris_ai import Runner, VerisConfig, ToolCallOptions, ResponseExpectation

config = VerisConfig(
    tool_options={
        "calculator": ToolCallOptions(
            response_expectation=ResponseExpectation.REQUIRED,
            cache_response=True,
            mode="tool",
        ),
        "search_web": ToolCallOptions(
            response_expectation=ResponseExpectation.NONE,
            cache_response=False,
            mode="spy",
        ),
    }
)

result = await Runner.run(agent, "Calculate and search", veris_config=config)
```

Notes:
- Runner is a drop‑in enhancement over OpenAI's Runner (full details in [OpenAI Agents Integration](#openai-agents-integration))
- See complete examples in [`examples/openai_agents_example.py`](examples/openai_agents_example.py)

## OpenAI Agents Integration

**Semantic Tag**: `openai-agents`

The SDK provides seamless integration with [OpenAI's agents library](https://github.com/openai/agents) through the `Runner` class, which extends OpenAI's Runner to intercept tool calls and route them through Veris's mocking infrastructure.

### Installation

```bash
# Install with agents support
uv add "veris-ai[agents]"
```

### Basic Usage

```python
from veris_ai import veris, Runner, VerisConfig
from agents import Agent, function_tool

# Define your tools
@function_tool
def calculator(x: int, y: int, operation: str = "add") -> int:
    """Performs arithmetic operations."""
    # ... implementation ...

# Create an agent with tools
agent = Agent(
    name="Assistant",
    model="gpt-4",
    tools=[calculator],
    instructions="You are a helpful assistant.",
)

# Use Veris Runner instead of OpenAI's Runner
result = await Runner.run(agent, "Calculate 10 + 5")

# Or with configuration
config = VerisConfig(include_tools=["calculator"])
result = await Runner.run(agent, "Calculate 10 + 5", veris_config=config)
```

### Selective Tool Interception

Control which tools are intercepted using VerisConfig:

```python
from veris_ai import Runner, VerisConfig

# Only intercept specific tools
config = VerisConfig(include_tools=["calculator", "search_web"])
result = await Runner.run(agent, "Process this", veris_config=config)

# Or exclude specific tools from interception
config = VerisConfig(exclude_tools=["get_weather"])
result = await Runner.run(agent, "Check weather", veris_config=config)
```

### Advanced Tool Configuration

Fine-tune individual tool behavior using `ToolCallOptions`:

```python
from veris_ai import Runner, VerisConfig, ResponseExpectation, ToolCallOptions

# Configure specific tool behaviors
config = VerisConfig(
    tool_options={
        "calculator": ToolCallOptions(
            response_expectation=ResponseExpectation.REQUIRED,  # Always expect response
            cache_response=True,  # Cache responses for identical calls
            mode="tool"  # Use tool mode (default)
        ),
        "search_web": ToolCallOptions(
            response_expectation=ResponseExpectation.NONE,  # Don't wait for response
            cache_response=False,
            mode="spy"  # Log calls but execute normally
        )
    }
)

result = await Runner.run(agent, "Calculate and search", veris_config=config)
```

**ToolCallOptions Parameters**:
- `response_expectation`: Control response behavior
  - `AUTO` (default): Automatically determine based on context
  - `REQUIRED`: Always wait for mock response
  - `NONE`: Don't wait for response
- `cache_response`: Cache responses for identical tool calls
- `mode`: Tool execution mode
  - `"tool"` (default): Standard tool execution
  - `"function"`: Function mode

**Key Features**:
- **Drop-in replacement**: Use `Runner` from veris_ai instead of OpenAI's Runner
- **Extends OpenAI Runner**: Inherits all functionality while adding Veris capabilities
- **Automatic session management**: Integrates with Veris session IDs
- **Selective mocking**: Include or exclude specific tools from interception

**Implementation**: See [`src/veris_ai/agents_wrapper.py`](src/veris_ai/agents_wrapper.py) for the integration logic and [`examples/openai_agents_example.py`](examples/openai_agents_example.py) for complete examples.

## FastAPI MCP Integration

**Semantic Tag**: `fastapi-mcp`

Expose FastAPI endpoints as MCP tools for AI agent consumption using HTTP transport.

```python
from fastapi import FastAPI
from veris_ai import veris

app = FastAPI()

# Enable MCP integration with HTTP transport
veris.set_fastapi_mcp(
    fastapi=app,
    name="My API Server",
    include_operations=["get_users", "create_user"],
    exclude_tags=["internal"]
)

# Mount the MCP server with HTTP transport (recommended)
veris.fastapi_mcp.mount_http()
```

**Key Features**:
- **HTTP Transport**: Uses Streamable HTTP protocol for better session management
- **Automatic schema conversion**: FastAPI OpenAPI → MCP tool definitions
- **Session management**: Bearer token → session ID mapping
- **Filtering**: Include/exclude operations and tags
- **Authentication**: OAuth2 integration

**Transport Protocol**: The SDK uses HTTP transport (via `mount_http()`) which implements the MCP Streamable HTTP specification, providing robust connection handling and fixing session routing issues with concurrent connections.

**Configuration Reference**: See function signature in [`src/veris_ai/tool_mock.py`](src/veris_ai/tool_mock.py) for all `set_fastapi_mcp()` parameters.

## Utility Functions

**Semantic Tag**: `json-schema-utils`

```python
from veris_ai.utils import extract_json_schema

# Schema extraction from types
user_schema = extract_json_schema(User)  # Pydantic models
list_schema = extract_json_schema(List[str])  # Generics
```

**Supported Types**: Built-in types, generics (List, Dict, Union), Pydantic models, TypedDict, forward references.

**Implementation**: See [`src/veris_ai/utils.py`](src/veris_ai/utils.py) for type conversion logic.

## Development

**Semantic Tag**: `development-setup`

**Requirements**: Python 3.11+, `uv` package manager

```bash
# Install with dev dependencies
uv add "veris-ai[dev]"

# Quality checks
ruff check --fix .    # Lint and format
pytest --cov=veris_ai # Test with coverage
```

**Testing & Architecture**: See [`tests/README.md`](tests/README.md) for test structure, fixtures, and coverage strategies. See [`src/veris_ai/README.md`](src/veris_ai/README.md) for module architecture and implementation flows.

## Module Architecture

**Semantic Tag**: `module-architecture`

**Core Modules**: `tool_mock` (mocking), `api_client` (centralized API), `agents_wrapper` (OpenAI agents integration), `jaeger_interface` (trace queries), `utils` (schema conversion)

**Complete Architecture**: See [`src/veris_ai/README.md`](src/veris_ai/README.md) for module overview, implementation flows, and configuration details. 

## Jaeger Trace Interface

**Semantic Tag**: `jaeger-query-api`

```python
from veris_ai.jaeger_interface import JaegerClient

client = JaegerClient("http://localhost:16686")
traces = client.search(service="veris-agent", tags={"error": "true"})
```

**Complete Guide**: See [`src/veris_ai/jaeger_interface/README.md`](src/veris_ai/jaeger_interface/README.md) for API reference, filtering strategies, and architecture details.

---

**License**: MIT License - see [LICENSE](LICENSE) file for details. 