# Freeplay Python LangGraph

Freeplay integration for LangGraph and LangChain.

## Installation

```bash
pip install freeplay-python-langgraph
```

## Usage

```python
from freeplay_python_langgraph import FreeplayLangGraph

# Initialize Freeplay observability
FreeplayLangGraph.initialize_observability(
    freeplay_api_url="https://api.freeplay.ai",
    freeplay_api_key="your-api-key",
    project_id="your-project-id",
    environment="latest"
)

# Now your LangGraph and LangChain applications will be automatically traced
```

## Features

- Automatic OpenTelemetry instrumentation for LangChain and LangGraph
- Trace visualization in Freeplay dashboard
- Support for all LangChain providers

## License

See LICENSE file for details.

