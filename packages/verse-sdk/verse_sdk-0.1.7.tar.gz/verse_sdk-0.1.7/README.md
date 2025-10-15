# Verse Python SDK

A Python SDK for observability and tracing in AI applications.

## Quick Start

```python
from verse_sdk import verse

# Initialize the SDK
verse.init(
    app_name="my-app",
    environment="development",
    exporters=[verse.exporters.console()],
    vendor="pydantic_ai",
    version="1.0.0"
)

# Use context managers (or decorators) for tracing
def my_function():
    with (
        verse.trace() as trace,
        verse.span() as span,
        verse.generation() as generation,
    ):
        # Your code here
        pass
```

## Initialization

| Argument      | Type              | Required | Description                                    |
|---------------|-------------------|----------|------------------------------------------------|
| `app_name`    | `str`             | Yes      | Identifies your observability project          |
| `environment` | `str`             | No       | Environment classification (dev, prod, etc.)  |
| `exporters`   | `list[Exporter]`  | Yes      | OpenTelemetry data exporters                   |
| `vendor`      | `str`             | Yes      | Enables auto-instrumentation for LLM clients  |
| `version`     | `str`             | No       | Application version                            |

## Exporters

On any exporter, you can filter outbound data using scopes:

```python
console_for_agent_a = verse.exporters.console({"scopes": ["agent-a"]})
console_for_agent_b = verse.exporters.console({"scopes": ["agent-b"]})
```

While not all exporters use config otherwise, `scopes` is a globally accepted attribute.

### Console
Print observations to terminal:
```python
verse.exporters.console()
```

### Langfuse
Push trace data to Langfuse:
```python
# With explicit configuration
verse.exporters.langfuse({
    "host": "https://cloud.langfuse.com",
    "private_key": "your-private-key",
    "public_key": "your-public-key",
    "region": "us-east-1"
})

# Or use environment variables
verse.exporters.langfuse()
```

## Context Managers

Automatically track spans and manage observability scope:

```python
def my_function():
    with (
        verse.trace() as trace,
        verse.span() as span,
        verse.generation() as generation,
    ):
        # Context managers accept any argument from their respective Context model
        trace.session("user-123").scope("agent-a")
        span.input("processing data").level("info")
        generation.model("gpt-4").vendor("openai")

def my_function_2():
    with (
        verse.trace(session="user-123", scope="agent-a"),
        verse.span(input="processing_data", level="info"),
        verse.generation(model="gpt-4", vendor="openai"),
    ):
        pass
```

Supports attributes on init or collected afterwards using each observation model's own API.

## Decorators

Instrument functions with minimal code changes:

```python
@observe_trace()
@observe_span() # or just @observe()
@observe_tool()
@observe_generation()
def my_function():
    pass
```

## Context Models

All contexts inherit these methods:

- `error(exception)` - Record an error
- `score(score)` - Add evaluation score
- `metadata(data)` - Add metadata
- `set_attributes(**kwargs)` - Set custom attributes

### TraceContext
Top-level operation context for tracing complete workflows.

**Methods:**
- `input(data)` - Set trace input
- `output(data)` - Set trace output
- `session(session_id)` - Set session identifier
- `scope(scope)` - Set trace scope
- `user(user_id)` - Set user identifier
- `tags(tags)` - Add trace tags
- `update(**kwargs)` - Update with additional attributes

**Example:**
```python
with verse.trace() as trace:
    trace.session("user-123").scope("agent-a").input("Hello world")
```

### SpanContext
Regular span context for sub-operations.

**Methods:**
- `input(data)` - Set span input
- `output(data)` - Set span output
- `level(level)` - Set observation level
- `status_message(message)` - Set status message
- `event(name, level="info", **attrs)` - Add event with metadata

**Example:**
```python
with verse.span() as span:
    span.input("processing").level("info").event("step_completed", level="debug")
```

### GenerationContext
Specialized context for LLM operations (inherits from SpanContext).

**Methods:**
- `input(content)` - Set generation prompt
- `output(content)` - Set generation output
- `model(model_name)` - Set model used
- `vendor(vendor)` - Set model vendor
- `usage(usage)` - Set token usage metrics

**Example:**
```python
with verse.generation() as gen:
    gen.model("gpt-4").vendor("openai").input("Hello").output("Hi there!")
```

## Integrations

### LiteLLM
Auto-instruments LLM calls when `vendor="litellm"`:

**Supported:**
- Both `completition` and `acompletion` functions

### Pydantic AI
Auto-instruments LLM calls when `vendor="pydantic_ai"`:

**Supported:**
- `Agent.run()` calls
- Text-based prompts and instructions
