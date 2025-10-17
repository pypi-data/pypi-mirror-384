# coagent-client

A Python client library for interacting with Coagent services.

## Installation

```bash
pip install infinyon-coagent-client
```

## Usage

```python
client = CoagentClient()

# Session-based logging with structured data
client.log_session_start("session123", "Hello world", prompt_number=1)
client.log_llm_response("session123", "Hi there", 1, 1,
    input_tokens=10, output_tokens=5)
client.log_error("session123", 1, 1, "Connection failed",
    error_type="network")
```

## Development

This package is part of the coagent-python-client workspace.