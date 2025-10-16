"""
Wipro AI Chat Model for LangChain
Complete implementation with tool calling support
"""

from typing import Any, Dict, Iterator, List, Optional, Tuple
import json
import re
import uuid
import os

import requests
from pydantic import Field, SecretStr, model_validator, ConfigDict

from langchain_core.callbacks.manager import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult


class ChatWiproAI(BaseChatModel):
    """
    Wipro AI chat model for LangChain.
    
    Example:
        .. code-block:: python
        
            from langchain_wiproai import ChatWiproAI
            
            # Initialize with required parameters
            llm = ChatWiproAI(
                model="gpt-4o",
                api_token="your-token-here"
            )
            
            # Or with all parameters
            llm = ChatWiproAI(
                model="gpt-4o",
                api_token="your-token-here",
                api_url="https://api.waip.wiprocms.com/v1.1/skills/completion/query",
                temperature=0.7,
                max_output_tokens=1500,
                top_p=0.9,
                top_k=5
            )
            
            # Simple usage
            response = llm.invoke("Hello!")
            print(response.content)
            
            # With tools
            from langchain_core.tools import tool
            
            @tool
            def get_weather(location: str) -> str:
                \"\"\"Get the weather for a location.\"\"\"
                return f"Weather in {location}: Sunny, 72°F"
            
            llm_with_tools = llm.bind_tools([get_weather])
            response = llm_with_tools.invoke("What's the weather in Paris?")
            print(response.tool_calls)
    """

    model_name: str = Field(
        default="gpt-4o",
        description="Model name to use for completions (e.g., 'gpt-4o', 'gpt-3.5-turbo')"
    )
    
    api_token: Optional[SecretStr] = Field(
        default=None,
        description="Wipro AI API authentication token. Can also be set via WIPROAI_API_TOKEN environment variable"
    )
    
    api_url: str = Field(
        default="https://api.waip.wiprocms.com/v1.1/skills/completion/query",
        description="Wipro AI API endpoint URL"
    )
    
    temperature: float = Field(
        default=0.0,
        ge=0.0,
        le=2.0,
        description="Temperature for response generation (0.0 to 2.0)"
    )
    
    max_output_tokens: int = Field(
        default=2000,
        ge=1,
        description="Maximum number of tokens to generate"
    )
    
    top_p: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Top-p (nucleus) sampling parameter (0.0 to 1.0)"
    )
    
    top_k: int = Field(
        default=1,
        ge=1,
        description="Top-k sampling parameter (minimum 1)"
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @model_validator(mode='after')
    def validate_api_token(self) -> 'ChatWiproAI':
        """Validate that api_token is provided either directly or via environment variable."""
        if self.api_token is None:
            # Try to get from environment variable
            token = os.getenv("WIPROAI_API_TOKEN")
            if token:
                self.api_token = SecretStr(token)
        elif isinstance(self.api_token, str):
            # Convert string to SecretStr if needed
            self.api_token = SecretStr(self.api_token)
        
        return self

    @property
    def _llm_type(self) -> str:
        """Return type of chat model."""
        return "wipro_ai"

    @property
    def _identifying_params(self) -> Dict[str, Any]:
        """Return identifying parameters."""
        return {
            "model_name": self.model_name,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "api_url": self.api_url,
        }

    def _convert_messages_to_api_format(self, messages: List[BaseMessage]) -> List[Dict[str, str]]:
        """Convert LangChain messages to Wipro AI API format."""
        api_messages = []
        
        for msg in messages:
            if isinstance(msg, SystemMessage):
                api_messages.append({"role": "system", "content": msg.content})
            elif isinstance(msg, HumanMessage):
                api_messages.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage):
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    tool_call_text = msg.content if msg.content else ""
                    for tc in msg.tool_calls:
                        tool_call_text += f"\n\nCalled tool: {tc['name']}\nWith arguments: {json.dumps(tc['args'])}"
                    api_messages.append({"role": "assistant", "content": tool_call_text})
                else:
                    api_messages.append({"role": "assistant", "content": msg.content})
            elif isinstance(msg, ToolMessage):
                tool_result = f"Tool '{msg.name}' returned:\n{msg.content}"
                api_messages.append({"role": "user", "content": tool_result})
        
        return api_messages

    def _extract_tool_calls(self, content: str, available_tools: List) -> Tuple[str, List[Dict]]:
        """
        Extract tool calls from LLM response.
        
        Args:
            content: The raw content from the LLM
            available_tools: List of available tool objects
            
        Returns:
            Tuple of (cleaned_content, list of tool_calls)
        """
        if not available_tools:
            return content, []

        tool_calls = []
        cleaned_content = content
        tool_names = {t.name for t in available_tools}

        # Pattern 1: JSON in markdown code blocks
        code_block_pattern = r'```(?:json)?\s*(\{[^`]+\})\s*```'
        code_blocks = re.findall(code_block_pattern, content, re.DOTALL)

        for block in code_blocks:
            try:
                tool_data = json.loads(block.strip())
                if isinstance(tool_data, dict) and "tool" in tool_data and "arguments" in tool_data:
                    if tool_data["tool"] in tool_names:
                        tool_calls.append({
                            "name": tool_data["tool"],
                            "args": tool_data["arguments"],
                            "id": f"call_{uuid.uuid4().hex[:8]}"
                        })
                        cleaned_content = re.sub(
                            r'```(?:json)?\s*' + re.escape(block) + r'\s*```',
                            '',
                            cleaned_content,
                            flags=re.DOTALL
                        ).strip()
            except json.JSONDecodeError:
                continue

        # Pattern 2: JSON anywhere in text
        if not tool_calls:
            json_pattern = r'\{[^{}]*?"tool"\s*:\s*"([^"]+)"[^{}]*?"arguments"\s*:\s*\{[^}]*\}[^{}]*\}'
            matches = re.finditer(json_pattern, content, re.DOTALL)

            for match in matches:
                try:
                    json_str = match.group(0)
                    tool_data = json.loads(json_str)
                    if isinstance(tool_data, dict) and "tool" in tool_data and "arguments" in tool_data:
                        if tool_data["tool"] in tool_names:
                            tool_calls.append({
                                "name": tool_data["tool"],
                                "args": tool_data["arguments"],
                                "id": f"call_{uuid.uuid4().hex[:8]}"
                            })
                            cleaned_content = content.replace(json_str, '').strip()
                            cleaned_content = re.sub(
                                r'^(Before|Let me|I will|I\'ll|Now)[^.!?]*[.!?]\s*',
                                '',
                                cleaned_content,
                                flags=re.IGNORECASE
                            ).strip()
                            break
                except json.JSONDecodeError:
                    continue

        # Pattern 3: Entire response is JSON
        if not tool_calls:
            try:
                tool_data = json.loads(content.strip())
                if isinstance(tool_data, dict) and "tool" in tool_data and "arguments" in tool_data:
                    if tool_data["tool"] in tool_names:
                        tool_calls.append({
                            "name": tool_data["tool"],
                            "args": tool_data["arguments"],
                            "id": f"call_{uuid.uuid4().hex[:8]}"
                        })
                        cleaned_content = ""
            except json.JSONDecodeError:
                pass

        return cleaned_content, tool_calls

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        """Generate response from Wipro AI."""

        if not self.api_token:
            raise ValueError(
                "Wipro AI API token not found. Please provide it as a parameter or set the WIPROAI_API_TOKEN environment variable."
            )
        
        # Convert messages to API format
        api_messages = self._convert_messages_to_api_format(messages)
        available_tools = kwargs.get('tools', [])
        
        # Add tool instructions if tools are available
        if available_tools:
            tool_descriptions = []
            for t in available_tools:
                params = ""
                if hasattr(t, 'args_schema') and t.args_schema:
                    try:
                        if isinstance(t.args_schema, dict):
                            schema = t.args_schema
                        elif hasattr(t.args_schema, 'model_json_schema'):
                            schema = t.args_schema.model_json_schema()
                        elif hasattr(t.args_schema, 'schema'):
                            schema = t.args_schema.schema()
                        else:
                            schema = {}
                        
                        if 'properties' in schema:
                            param_list = []
                            for param_name, param_info in schema['properties'].items():
                                param_type = param_info.get('type', 'string')
                                param_desc = param_info.get('description', '')
                                param_list.append(f"    - {param_name} ({param_type}): {param_desc}")
                            if param_list:
                                params = "\n" + "\n".join(param_list)
                    except Exception:
                        pass
                
                tool_descriptions.append(f"- {t.name}: {t.description}{params}")
            
            tool_instruction = f"""You are an AI assistant with access to tools.

Available tools:
{chr(10).join(tool_descriptions)}

To use a tool, respond with ONLY a JSON object:
{{"tool": "tool_name", "arguments": {{"param": "value"}}}}

RULES:
1. Output ONLY the JSON when calling a tool (no explanation)
2. Do NOT use markdown code blocks
3. After tool execution, provide a natural language response
"""
            
            if api_messages and api_messages[0]["role"] == "system":
                api_messages[0]["content"] += "\n\n" + tool_instruction
            else:
                api_messages.insert(0, {"role": "system", "content": tool_instruction})

        # Prepare API request
        payload = {
            "messages": api_messages,
            "skill_parameters": {
                "model_name": self.model_name,
                "temperature": self.temperature,
                "max_output_tokens": self.max_output_tokens,
                "top_p": self.top_p,
                "top_k": self.top_k
            },
            "stream_response": False
        }

        headers = {
            "Authorization": f"Bearer {self.api_token.get_secret_value()}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=120
            )
            response.raise_for_status()
            result = response.json()

            # Extract content from various response formats
            content = ""
            if "choices" in result and result["choices"]:
                content = result["choices"][0].get("message", {}).get("content", "")
            elif "response" in result:
                content = result["response"]
            elif "content" in result:
                content = result["content"]
            elif "data" in result and "content" in result["data"]:
                content = result["data"]["content"]
            else:
                content = str(result)

            # Extract tool calls
            cleaned_content, tool_calls = self._extract_tool_calls(content, available_tools)

            if tool_calls:
                message = AIMessage(
                    content=cleaned_content if cleaned_content else "",
                    tool_calls=tool_calls
                )
            else:
                message = AIMessage(content=content)

            return ChatResult(generations=[ChatGeneration(message=message)])

        except requests.exceptions.RequestException as e:
            error_message = AIMessage(content=f"API Error: {str(e)}")
            return ChatResult(generations=[ChatGeneration(message=error_message)])
        except Exception as e:
            error_message = AIMessage(content=f"Error: {str(e)}")
            return ChatResult(generations=[ChatGeneration(message=error_message)])

    def bind_tools(self, tools: List, **kwargs) -> "ChatWiproAI":
        """Bind tools to the model."""
        return self.bind(tools=tools, **kwargs)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """Stream response from Wipro AI."""
        # This is a placeholder for streaming implementation.
        # The Wipro AI API must support streaming responses for this to work.
        # You would typically use `requests.post(..., stream=True)`
        # and iterate over the response chunks.
        raise NotImplementedError("Streaming is not yet supported by ChatWiproAI.")

    async def _astream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        """Async stream response from Wipro AI."""
        raise NotImplementedError("Async streaming is not yet supported by ChatWiproAI.")