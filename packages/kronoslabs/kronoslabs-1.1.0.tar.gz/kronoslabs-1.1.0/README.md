# Kronos Labs Python Client

Official Python client for the Kronos Labs API.

## Installation

```bash
pip install kronoslabs
```

## Quick Start

```python
from kronoslabs import KronosLabs

# Initialize the client
client = KronosLabs(api_key="your-api-key-here")

# Non-streaming chat completion with hyperion model
response = client.chat.completions.create(
    prompt="Hello, how are you?",
    model="hyperion",  # or "hermes"
    temperature=0.7,
    is_stream=False
)

print(response.choices[0].message.content)

# Streaming chat completion with hermes model
stream = client.chat.completions.create(
    prompt="Tell me a story",
    model="hermes",
    temperature=0.7,
    is_stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

## Features

- Simple and intuitive API similar to OpenAI's ChatGPT client
- Support for multiple models: `hyperion` and `hermes`
- Support for both streaming and non-streaming responses
- Automatic handling of API authentication
- Comprehensive error handling
- Type hints for better IDE support

## API Reference

### Initialize Client

```python
client = KronosLabs(api_key="your-api-key")
```

### Chat Completions

```python
response = client.chat.completions.create(
    messages=[],  # Optional: list of message dicts
    prompt="Your prompt here",  # Required: the prompt text
    model="hyperion",  # Optional: "hyperion" or "hermes" (default: "hyperion")
    temperature=0.7,  # Optional: controls randomness (0.0-2.0)
    is_stream=False,  # Optional: enable streaming
    tool=True  # Optional: enable tool usage
)
```

#### Parameters

- `messages` (list, optional): List of message dictionaries with 'role' and 'content' keys
- `prompt` (str, required): The prompt text to send to the model
- `model` (str, optional): Model to use - either `"hyperion"` or `"hermes"`. Default: `"hyperion"`
- `temperature` (float, optional): Controls randomness in the response (0.0-2.0). Default: 0.7
- `is_stream` (bool, optional): Enable streaming responses. Default: False
- `tool` (bool, optional): Enable tool usage. Default: True

#### Response Format

Non-streaming response:

```python
{
    "id": "chatcmpl_...",
    "object": "chat.completion",
    "created": 1234567890,
    "model": "hyperion-1.5b-chat",
    "choices": [{
        "index": 0,
        "message": {
            "role": "assistant",
            "content": "Response text"
        },
        "finish_reason": "stop"
    }],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30
    }
}
```

Streaming response (yields chunks):

```python
{
    "id": "chatcmpl_...",
    "object": "chat.completion.chunk",
    "created": 1234567890,
    "model": "hyperion-1.5b-chat",
    "choices": [{
        "index": 0,
        "delta": {
            "content": "token"
        },
        "finish_reason": null
    }]
}
```

## Error Handling

```python
from kronoslabs import KronosLabs, APIError, AuthenticationError

client = KronosLabs(api_key="your-api-key")

try:
    response = client.chat.completions.create(prompt="Hello")
except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except APIError as e:
    print(f"API error: {e.message}, Status: {e.status_code}")
```

## License

MIT License
