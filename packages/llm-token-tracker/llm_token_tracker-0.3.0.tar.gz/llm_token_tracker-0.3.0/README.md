# llm-token-tracker

A Python package to track token usage in LLM interactions.

## Installation

```bash
pip install llm-token-tracker
```

## Usage

```python
from llm_token_tracker import wrap_llm
from xai_sdk import Client
import logging

# Create and wrap a chat for token tracking
client = Client()
chat = client.chat.create(model="grok-3")
wrapped_chat = wrap_llm(chat)

response = wrapped_chat.sample("Hello, how are you?")
print(response.content)
# Console will log: Total tokens used in context: X

# For conversation context
wrapped_chat.append(system("You are Grok, a highly intelligent AI."))
wrapped_chat.append(user("What is the meaning of life?"))
response = wrapped_chat.sample()
print(response.content)
```

### Configuration Options

`wrap_llm` accepts several parameters to customize logging:

- `verbosity`: `"minimum"` (default), `"detailed"`, or `"max"`
  - `"minimum"`: Logs only total tokens used.
  - `"detailed"`: Logs a detailed usage summary.
  - `"max"`: Logs the full history of all token usages.
- `logger`: Optional `logging.Logger` instance. If provided, uses the logger instead of printing to console.
- `log_level`: Logging level (default `logging.INFO`).
- `quiet`: If `True`, disables all logging.

Example with custom logger:

```python
import logging

logger = logging.getLogger("my_llm_logger")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
logger.addHandler(handler)

wrapped_chat = wrap_llm(chat, logger=logger, verbosity="detailed")
```

Note: Requires XAI_API_KEY environment variable set for authentication.
