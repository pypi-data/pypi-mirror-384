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

Note: Requires XAI_API_KEY environment variable set for authentication.
