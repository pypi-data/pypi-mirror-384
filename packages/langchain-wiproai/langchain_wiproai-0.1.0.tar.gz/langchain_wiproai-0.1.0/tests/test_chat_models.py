"""
Unit tests for ChatWiproAI model
"""

import pytest
import os
from langchain_wiproai import ChatWiproAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


def test_initialization_with_all_params():
    """Test model initialization with all parameters."""
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token",
        temperature=0.5,
        max_output_tokens=1500,
        top_p=0.9,
        top_k=5
    )
    assert llm.model_name == "gpt-4o"
    assert llm.temperature == 0.5
    assert llm.max_output_tokens == 1500
    assert llm.top_p == 0.9
    assert llm.top_k == 5


def test_initialization_minimum_params():
    """Test model initialization with minimum required parameters."""
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token"
    )
    assert llm.model_name == "gpt-4o"
    assert llm.temperature == 0.0  # Default value
    assert llm.max_output_tokens == 2000  # Default value


def test_initialization_with_env_var():
    """Test model initialization using environment variable for token."""
    # Set environment variable
    os.environ["WIPROAI_API_TOKEN"] = "env-test-token"

    llm = ChatWiproAI(model_name="gpt-4o")
    assert llm.model_name == "gpt-4o"
    assert llm.api_token.get_secret_value() == "env-test-token"

    # Clean up
    del os.environ["WIPROAI_API_TOKEN"]


def test_initialization_missing_token():
    """Test that initialization works with empty token from env."""
    # Make sure env var is not set
    if "WIPROAI_API_TOKEN" in os.environ:
        del os.environ["WIPROAI_API_TOKEN"]

    # Should initialize with empty token (will fail at API call time)
    llm = ChatWiproAI(model_name="gpt-4o")
    assert llm.model_name == "gpt-4o"


def test_identifying_params():
    """Test identifying parameters."""
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token",
        temperature=0.7
    )
    params = llm._identifying_params

    assert "model_name" in params
    assert "temperature" in params
    assert "max_output_tokens" in params
    assert "top_p" in params
    assert "top_k" in params
    assert params["model_name"] == "gpt-4o"
    assert params["temperature"] == 0.7


def test_llm_type():
    """Test LLM type identifier."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    assert llm._llm_type == "wipro_ai"


def test_message_conversion_human():
    """Test human message format conversion."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    messages = [HumanMessage(content="Hello")]
    api_messages = llm._convert_messages_to_api_format(messages)
    
    assert len(api_messages) == 1
    assert api_messages[0]["role"] == "user"
    assert api_messages[0]["content"] == "Hello"


def test_message_conversion_system():
    """Test system message format conversion."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    messages = [SystemMessage(content="You are a helpful assistant")]
    api_messages = llm._convert_messages_to_api_format(messages)
    
    assert len(api_messages) == 1
    assert api_messages[0]["role"] == "system"
    assert api_messages[0]["content"] == "You are a helpful assistant"


def test_message_conversion_ai():
    """Test AI message format conversion."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    messages = [AIMessage(content="Hello! How can I help?")]
    api_messages = llm._convert_messages_to_api_format(messages)
    
    assert len(api_messages) == 1
    assert api_messages[0]["role"] == "assistant"
    assert api_messages[0]["content"] == "Hello! How can I help?"


def test_message_conversion_mixed():
    """Test multiple message types conversion."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    messages = [
        SystemMessage(content="You are helpful"),
        HumanMessage(content="Hi"),
        AIMessage(content="Hello!"),
        HumanMessage(content="How are you?")
    ]
    api_messages = llm._convert_messages_to_api_format(messages)
    
    assert len(api_messages) == 4
    assert api_messages[0]["role"] == "system"
    assert api_messages[1]["role"] == "user"
    assert api_messages[2]["role"] == "assistant"
    assert api_messages[3]["role"] == "user"


def test_tool_call_extraction_json():
    """Test extracting tool calls from pure JSON response."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    
    # Mock tool
    class MockTool:
        name = "get_weather"
    
    content = '{"tool": "get_weather", "arguments": {"location": "Paris"}}'
    cleaned, tool_calls = llm._extract_tool_calls(content, [MockTool()])
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["name"] == "get_weather"
    assert tool_calls[0]["args"]["location"] == "Paris"
    assert cleaned == ""


def test_tool_call_extraction_with_explanation():
    """Test extracting tool calls when LLM adds explanation."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    
    class MockTool:
        name = "search_database"
    
    content = 'Let me search for that. {"tool": "search_database", "arguments": {"query": "test"}}'
    cleaned, tool_calls = llm._extract_tool_calls(content, [MockTool()])
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["name"] == "search_database"
    assert tool_calls[0]["args"]["query"] == "test"


def test_tool_call_extraction_markdown():
    """Test extracting tool calls from markdown code blocks."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    
    class MockTool:
        name = "calculate"
    
    content = '```json\n{"tool": "calculate", "arguments": {"expression": "2+2"}}\n```'
    cleaned, tool_calls = llm._extract_tool_calls(content, [MockTool()])
    
    assert len(tool_calls) == 1
    assert tool_calls[0]["name"] == "calculate"
    assert tool_calls[0]["args"]["expression"] == "2+2"


def test_tool_call_extraction_no_tools():
    """Test that no extraction happens when no tools are available."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    
    content = '{"tool": "some_tool", "arguments": {"key": "value"}}'
    cleaned, tool_calls = llm._extract_tool_calls(content, [])
    
    assert len(tool_calls) == 0
    assert cleaned == content


def test_tool_call_extraction_invalid_tool():
    """Test that invalid tool names are ignored."""
    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    
    class MockTool:
        name = "valid_tool"
    
    content = '{"tool": "invalid_tool", "arguments": {"key": "value"}}'
    cleaned, tool_calls = llm._extract_tool_calls(content, [MockTool()])
    
    assert len(tool_calls) == 0


def test_different_models():
    """Test initialization with different model names."""
    models = ["gpt-4o", "gpt-3.5-turbo", "claude-3-sonnet", "custom-model"]

    for model_name in models:
        llm = ChatWiproAI(model_name=model_name, api_token="test-token")
        assert llm.model_name == model_name


def test_temperature_bounds():
    """Test temperature parameter bounds."""
    # Valid temperatures
    llm1 = ChatWiproAI(model_name="gpt-4o", api_token="test", temperature=0.0)
    assert llm1.temperature == 0.0

    llm2 = ChatWiproAI(model_name="gpt-4o", api_token="test", temperature=1.0)
    assert llm2.temperature == 1.0

    llm3 = ChatWiproAI(model_name="gpt-4o", api_token="test", temperature=2.0)
    assert llm3.temperature == 2.0

    # Invalid temperature (should raise validation error)
    with pytest.raises(Exception):  # Pydantic validation error
        ChatWiproAI(model_name="gpt-4o", api_token="test", temperature=2.5)


def test_custom_api_url():
    """Test using custom API URL."""
    custom_url = "https://custom.api.com/v1/chat"
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token",
        api_url=custom_url
    )
    assert llm.api_url == custom_url


def test_max_output_tokens():
    """Test max_output_tokens parameter."""
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token",
        max_output_tokens=500
    )
    assert llm.max_output_tokens == 500


def test_top_p_parameter():
    """Test top_p parameter."""
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token",
        top_p=0.8
    )
    assert llm.top_p == 0.8


def test_top_k_parameter():
    """Test top_k parameter."""
    llm = ChatWiproAI(
        model_name="gpt-4o",
        api_token="test-token",
        top_k=10
    )
    assert llm.top_k == 10


def test_bind_tools():
    """Test binding tools to the model."""
    from langchain_core.tools import tool

    @tool
    def test_tool(query: str) -> str:
        """A test tool."""
        return "result"

    llm = ChatWiproAI(model_name="gpt-4o", api_token="test-token")
    llm_with_tools = llm.bind_tools([test_tool])
    
    # In recent LangChain versions, bind_tools returns a RunnableBinding
    from langchain_core.runnables.base import Runnable
    assert isinstance(llm_with_tools, Runnable)
    
    # The original model is the 'bound' attribute
    assert llm_with_tools.bound == llm


if __name__ == "__main__":
    pytest.main([__file__, "-v"])