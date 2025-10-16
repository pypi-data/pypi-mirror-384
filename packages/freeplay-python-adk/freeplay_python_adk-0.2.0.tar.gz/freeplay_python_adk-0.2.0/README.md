# Freeplay Python ADK

Freeplay integration for Google ADK (Agent Development Kit).

## Installation

```bash
pip install freeplay-python-adk
```

## Usage

```python
from freeplay_python_adk import FreeplayADK, FreeplayLLMAgent

# Initialize Freeplay observability
FreeplayADK.initialize_observability(
    freeplay_api_url="https://api.freeplay.ai",
    freeplay_api_key="your-api-key",
    project_id="your-project-id",
    environment="latest"
)

# Create an agent
agent = FreeplayLLMAgent(
    name="my_agent",
    description="An example agent"
)
```

## Features

- Seamless integration with Google ADK
- Automatic OpenTelemetry instrumentation
- Prompt template management through Freeplay
- Support for multiple LLM providers via LiteLLM

## License

See LICENSE file for details.

