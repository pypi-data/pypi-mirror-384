# llmeval - Python SDK for evaluate
## download the evaluate server from https://github.com/RGGH/evaluate

A Python client library for the evaluate LLM evaluation framework.

## Installation

```bash
pip install -e .
```

For development with all extras:
```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from llmeval import EvalClient

# Initialize the client
client = EvalClient(base_url="http://127.0.0.1:8080")

# Check server health
status = client.health_check()
print(status)

# Get available models
models = client.get_models()
print(f"Available models: {models}")

# Run a single evaluation
result = client.run_eval(
    model="gemini:gemini-2.5-pro",
    prompt="What is the capital of France?",
    expected="Paris",
    judge_model="gemini:gemini-2.5-pro"
)

print(f"Model output: {result.model_output}")
print(f"Judge verdict: {result.judge_verdict}")
print(f"Passed: {result.passed}")
```

## Features

- ✅ Simple, intuitive API
- ✅ Type-safe with Pydantic models
- ✅ Batch evaluation support
- ✅ Real-time WebSocket streaming
- ✅ Jupyter notebook integration
- ✅ pandas DataFrame utilities
- ✅ Comprehensive error handling
- ✅ Context manager support

## Documentation

See the `examples/` directory for more usage examples:
- `basic_usage.py` - Simple examples
- `advanced_usage.py` - Advanced patterns
- `streaming_example.py` - WebSocket streaming
- `jupyter_example.ipynb` - Jupyter notebook

## Requirements

- Python 3.8+
- requests
- pydantic
- websockets
- pandas

## License

MIT License
