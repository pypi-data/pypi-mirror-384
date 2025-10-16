# AIClient - Python Client for Intelligence.io API

[![PyPI version](https://img.shields.io/pypi/v/aiclient.svg)](https://pypi.org/project/aiclient/)
[![Python versions](https://img.shields.io/pypi/pyversions/aiclient.svg)](https://pypi.org/project/aiclient/)
[![License](https://img.shields.io/pypi/l/aiclient.svg)](https://opensource.org/licenses/MIT)

AIClient is a Python library that provides a simple interface to interact with Intelligence.io's AI API. It simplifies the process of sending requests to various AI models and handling responses, making it easy to integrate AI capabilities into your Python applications.

## Features

- 🚀 Easy-to-use interface for Intelligence.io API
- 🤖 Support for multiple AI models
- 🔑 Secure API key management
- 🔄 Streamlined model selection process
- 💬 Simple query-response workflow
- 🛠️ Error handling and validation

## Installation

Install the package using pip:

```bash
pip install FuClientForExam
```

## Getting Started

### Prerequisites

1. Sign up for an account at [Intelligence.io](https://intelligence.io.solutions/)
2. Obtain your API key from your account dashboard

### Basic Usage

```python
from FuClientForExam import AIClient

# Initialize the client with your API key
client = AIClient(api_key="your_api_key_here")

# Send a query to the AI
response = client.ask_AI("What is the capital of France?")
print(response)
```

### Selecting a Model

```python
# List available models and select one interactively
client.set_model()

# Or set a model directly
client.set_model("deepseek-ai/DeepSeek-R1-0528")
```

## Documentation

### AIClient Class

#### `__init__(api_key: str)`

Initializes the AI client with your API key.

- `api_key`: Your Intelligence.io API key (required)

#### `set_model(model_name: str = None)`

Sets the AI model to use. If no model name is provided, it will list available models and prompt for selection.

- `model_name`: Optional name of the model to use directly

#### `ask_AI(message: str, raw: bool = False) -> str`

Sends a message to the AI and returns the response.

- `message`: The text to send to the AI
- `raw`: If True, returns the raw response without processing (default: False)
- Returns: The AI's response as a string

## Advanced Usage

### Handling Raw Responses

```python
# Get the raw response from the API
raw_response = client.ask_AI("Tell me about quantum computing", raw=True)
print("Raw response:", raw_response)
```

### Error Handling

```python
try:
    response = client.ask_AI("What is the meaning of life?")
    print(response)
except Exception as e:
    print(f"An error occurred: {str(e)}")
```

### Checking Available Models

```python
# This will print available models but not change the current selection
client.set_model()
```

## Examples

### Simple Chatbot

```python
from FuClientForExam import AIClient


def main():
   client = AIClient(api_key="your_api_key_here")

   print("AI Chatbot (type 'exit' to quit)")
   while True:
      user_input = input("You: ")
      if user_input.lower() == 'exit':
         break

      response = client.ask_AI(user_input)
      print(f"AI: {response}")


if __name__ == "__main__":
   main()
```

### Model Testing Utility

```python
from FuClientForExam import AIClient


def test_models(api_key, test_query="Explain quantum entanglement in simple terms"):
   client = AIClient(api_key=api_key)
   client.set_model()  # Show available models

   original_model = client.model

   # Get available models (re-run set_model to capture output)
   models = [...]  # You would collect models programmatically here

   print("\nTesting models with query:", test_query)
   for model in models:
      try:
         client.set_model(model)
         response = client.ask_AI(test_query)
         print(f"\n=== {model} ===\n{response[:200]}...")  # Print first 200 chars
      except Exception as e:
         print(f"Error with model {model}: {str(e)}")

   # Restore original model
   client.set_model(original_model)


if __name__ == "__main__":
   test_models("your_api_key_here")
```

## Best Practices

1. **Secure API Key Management**:
   - Never hardcode API keys in your source code
   - Use environment variables or secret management systems
   ```python
   import os
   api_key = os.getenv("INTELLIGENCE_API_KEY")
   client = AIClient(api_key=api_key)
   ```

2. **Rate Limiting**:
   - Implement appropriate rate limiting in your application
   - Handle API rate limit errors gracefully

3. **Error Handling**:
   - Always wrap API calls in try-except blocks
   - Implement retry logic for transient errors

4. **Model Selection**:
   - Test different models for your specific use case
   - Consider performance/cost tradeoffs when choosing models

## Troubleshooting

### Common Issues

1. **Authentication Errors**:
   - Verify your API key is correct
   - Ensure your account is active and has sufficient credits

2. **Model Not Available**:
   - Use `set_model()` to verify available models
   - Check the Intelligence.io status page for service disruptions

3. **Network Issues**:
   - Check your internet connection
   - Verify firewall/proxy settings allow outbound connections to `api.intelligence.io.solutions`

### Getting Help

For additional support, please contact:
- Intelligence.io Support: support@intelligence.io.solutions
- GitHub Issues: https://github.com/yourusername/aiclient/issues

## Contributing

We welcome contributions! Please see our [Contribution Guidelines](CONTRIBUTING.md) for details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

### v0.1.0 (Initial Release)
- Initial implementation of AIClient
- Basic model selection functionality
- Simple query-response interface

---

**Note**: This library is not officially affiliated with Intelligence.io. It's an unofficial client library created to simplify interaction with the Intelligence.io API.