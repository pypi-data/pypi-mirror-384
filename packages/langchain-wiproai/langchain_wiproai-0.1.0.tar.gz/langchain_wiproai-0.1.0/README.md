# langchain-wiproai

Wipro AI integration for LangChain, providing seamless access to Wipro AI models with full tool calling support.

## Installation

```bash
pip install langchain-wiproai
```

## Quick Start

```python
from langchain_wiproai import ChatWiproAI

# Initialize the model
llm = ChatWiproAI(
    api_token="your-api-token",
    model_name="gpt-4o",
    temperature=0.0
)

# Simple usage
response = llm.invoke("Hello, how are you?")
print(response.content)

# With tool calling
from langchain_core.tools import tool

@tool
def get_weather(location: str) -> str:
    \"\"\"Get the weather for a location.\"\"\"
    return f"The weather in {location} is sunny!"

llm_with_tools = llm.bind_tools([get_weather])
response = llm_with_tools.invoke("What's the weather in Paris?")
print(response.tool_calls)
```

## Configuration

### Environment Variables

You can set your API token as an environment variable:

```bash
export WIPROAI_API_TOKEN="your-api-token"
```

Then use without passing the token:

```python
from langchain_wiproai import ChatWiproAI

llm = ChatWiproAI()  # Will use WIPROAI_API_TOKEN from environment
```

### Parameters

- `api_token` (str): Your Wipro AI API token
- `api_url` (str): API endpoint URL (default: Wipro AI endpoint)
- `model_name` (str): Model to use (default: "gpt-4o")
- `temperature` (float): Temperature for generation (default: 0.0, range: 0.0-2.0)
- `max_output_tokens` (int): Maximum tokens to generate (default: 2000)
- `top_p` (float): Top-p sampling parameter (default: 1.0, range: 0.0-1.0)
- `top_k` (int): Top-k sampling parameter (default: 1)

## Advanced Usage

### Streaming

```python
for chunk in llm.stream("Tell me a story"):
    print(chunk.content, end="", flush=True)
```

### Async

```python
import asyncio

async def main():
    response = await llm.ainvoke("Hello!")
    print(response.content)

asyncio.run(main())
```

### With LangChain Agents

```python
from langchain.agents import create_react_agent
from langchain_wiproai import ChatWiproAI
from langchain_core.tools import tool

@tool
def calculator(expression: str) -> str:
    \"\"\"Calculate a mathematical expression.\"\"\"
    return str(eval(expression))

llm = ChatWiproAI(temperature=0)
agent = create_react_agent(llm, [calculator])
result = agent.invoke({"input": "What is 25 * 47?"})
```

## Features

- ✅ Full LangChain integration
- ✅ Tool/function calling support
- ✅ Streaming support
- ✅ Async support
- ✅ Automatic JSON tool call parsing
- ✅ Multiple response format handling
- ✅ Pydantic v2 compatibility