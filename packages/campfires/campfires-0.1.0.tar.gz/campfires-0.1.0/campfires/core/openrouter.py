"""
OpenRouter API integration for LLM capabilities in Campfires.
"""

import os
import json
import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Union, AsyncGenerator
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import MCP for protocol support
from ..mcp.protocol import MCPProtocol, MCPMessage
from ..mcp.transport import AsyncQueueTransport


logger = logging.getLogger(__name__)


@dataclass
class OpenRouterConfig:
    """Configuration for OpenRouter API."""
    api_key: str = None
    base_url: str = "https://openrouter.ai/api/v1"
    default_model: str = "openai/gpt-oss-20b:free"
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    def __post_init__(self):
        """Load API key from environment if not provided."""
        if self.api_key is None:
            self.api_key = os.getenv("OPENROUTER_API_KEY")
            if not self.api_key:
                raise ValueError("OPENROUTER_API_KEY environment variable is required")


class ChatMessage(BaseModel):
    """Represents a chat message."""
    role: str = Field(..., description="Role: system, user, or assistant")
    content: str = Field(..., description="Message content")
    name: Optional[str] = Field(None, description="Optional name for the message")


class ChatRequest(BaseModel):
    """Request for chat completion."""
    model: str = Field(..., description="Model to use")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    temperature: Optional[float] = Field(None, description="Temperature for sampling")
    top_p: Optional[float] = Field(None, description="Top-p for nucleus sampling")
    frequency_penalty: Optional[float] = Field(None, description="Frequency penalty")
    presence_penalty: Optional[float] = Field(None, description="Presence penalty")
    stop: Optional[Union[str, List[str]]] = Field(None, description="Stop sequences")
    stream: bool = Field(False, description="Whether to stream the response")


class ChatResponse(BaseModel):
    """Response from chat completion."""
    id: str
    object: str
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Optional[Dict[str, Any]] = None
    
    class Config:
        extra = "allow"  # Allow extra fields from the API response


class OpenRouterClient:
    """
    Client for interacting with OpenRouter API.
    """
    
    def __init__(self, config: OpenRouterConfig = None, mcp_protocol: Optional[MCPProtocol] = None):
        """
        Initialize OpenRouter client.
        
        Args:
            config: OpenRouter configuration
            mcp_protocol: Optional MCP protocol for communication
        """
        self.config = config or self._load_config()
        self.session: Optional[aiohttp.ClientSession] = None
        self.mcp_protocol = mcp_protocol
        
        # Request tracking
        self.request_count = 0
        self.total_tokens_used = 0
        self.last_request_time: Optional[datetime] = None
    
    def _load_config(self) -> OpenRouterConfig:
        """Load configuration from environment variables."""
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            raise ValueError("OPENROUTER_API_KEY environment variable is required")
        
        return OpenRouterConfig(
            api_key=api_key,
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_model=os.getenv("OPENROUTER_DEFAULT_MODEL", "anthropic/claude-3.5-sonnet"),
            max_tokens=int(os.getenv("OPENROUTER_MAX_TOKENS", "2000")),
            temperature=float(os.getenv("OPENROUTER_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("OPENROUTER_TIMEOUT", "30")),
            max_retries=int(os.getenv("OPENROUTER_MAX_RETRIES", "3")),
            retry_delay=float(os.getenv("OPENROUTER_RETRY_DELAY", "1.0"))
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close_session()
    
    async def start_session(self) -> None:
        """Start the HTTP session."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
    
    async def close_session(self) -> None:
        """Close the HTTP session."""
        if self.session:
            await self.session.close()
            self.session = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        return {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/campfires-ai/campfires",
            "X-Title": "Campfires Framework"
        }
    
    async def _make_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Make an HTTP request to the OpenRouter API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            
        Returns:
            Response data
        """
        if not self.session:
            await self.start_session()
        
        url = f"{self.config.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        for attempt in range(self.config.max_retries + 1):
            try:
                async with self.session.request(
                    method, 
                    url, 
                    headers=headers, 
                    json=data
                ) as response:
                    
                    self.request_count += 1
                    self.last_request_time = datetime.now()
                    
                    if response.status == 200:
                        result = await response.json()
                        
                        # Track token usage
                        if 'usage' in result and 'total_tokens' in result['usage']:
                            self.total_tokens_used += result['usage']['total_tokens']
                        
                        return result
                    
                    elif response.status == 429:  # Rate limit
                        if attempt < self.config.max_retries:
                            wait_time = self.config.retry_delay * (2 ** attempt)
                            logger.warning(f"Rate limited, waiting {wait_time}s before retry")
                            await asyncio.sleep(wait_time)
                            continue
                    
                    # Handle other errors
                    error_text = await response.text()
                    logger.error(f"API request failed: {response.status} - {error_text}")
                    
                    if response.status >= 500 and attempt < self.config.max_retries:
                        # Server error, retry
                        await asyncio.sleep(self.config.retry_delay)
                        continue
                    
                    raise aiohttp.ClientResponseError(
                        request_info=response.request_info,
                        history=response.history,
                        status=response.status,
                        message=error_text
                    )
            
            except aiohttp.ClientError as e:
                if attempt < self.config.max_retries:
                    logger.warning(f"Request failed, retrying: {e}")
                    await asyncio.sleep(self.config.retry_delay)
                    continue
                raise
        
        raise Exception(f"Max retries ({self.config.max_retries}) exceeded")
    
    async def chat_completion(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        **kwargs
    ) -> ChatResponse:
        """
        Create a chat completion.
        
        Args:
            messages: List of chat messages
            model: Model to use (defaults to config default)
            **kwargs: Additional parameters
            
        Returns:
            Chat completion response
        """
        request_data = ChatRequest(
            model=model or self.config.default_model,
            messages=messages,
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            temperature=kwargs.get('temperature', self.config.temperature),
            **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature']}
        )
        
        response_data = await self._make_request(
            "POST", 
            "/chat/completions", 
            request_data.model_dump(exclude_none=True)
        )
        
        return ChatResponse(**response_data)
    
    async def stream_chat_completion(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Create a streaming chat completion.
        
        Args:
            messages: List of chat messages
            model: Model to use
            **kwargs: Additional parameters
            
        Yields:
            Streaming response chunks
        """
        request_data = ChatRequest(
            model=model or self.config.default_model,
            messages=messages,
            stream=True,
            max_tokens=kwargs.get('max_tokens', self.config.max_tokens),
            temperature=kwargs.get('temperature', self.config.temperature),
            **{k: v for k, v in kwargs.items() if k not in ['max_tokens', 'temperature']}
        )
        
        if not self.session:
            await self.start_session()
        
        url = f"{self.config.base_url}/chat/completions"
        headers = self._get_headers()
        
        async with self.session.post(
            url, 
            headers=headers, 
            json=request_data.model_dump(exclude_none=True)
        ) as response:
            
            if response.status != 200:
                error_text = await response.text()
                raise aiohttp.ClientResponseError(
                    request_info=response.request_info,
                    history=response.history,
                    status=response.status,
                    message=error_text
                )
            
            async for line in response.content:
                line = line.decode('utf-8').strip()
                
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    
                    if data == '[DONE]':
                        break
                    
                    try:
                        chunk = json.loads(data)
                        yield chunk
                    except json.JSONDecodeError:
                        continue
    
    async def get_models(self) -> List[Dict[str, Any]]:
        """
        Get available models.
        
        Returns:
            List of available models
        """
        response = await self._make_request("GET", "/models")
        return response.get('data', [])
    
    async def simple_completion(
        self, 
        prompt: str, 
        model: str = None,
        system_prompt: str = None,
        **kwargs
    ) -> str:
        """
        Simple completion for a single prompt.
        
        Args:
            prompt: User prompt
            model: Model to use
            system_prompt: Optional system prompt
            **kwargs: Additional parameters
            
        Returns:
            Completion text
        """
        messages = []
        
        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        
        messages.append(ChatMessage(role="user", content=prompt))
        
        response = await self.chat_completion(messages, model, **kwargs)
        
        if response.choices and len(response.choices) > 0:
            return response.choices[0]['message']['content']
        
        return ""
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get client statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            'request_count': self.request_count,
            'total_tokens_used': self.total_tokens_used,
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
            'config': {
                'model': self.config.default_model,
                'max_tokens': self.config.max_tokens,
                'temperature': self.config.temperature
            }
        }
    
    async def send_mcp_message(self, message: str, channel: str = "llm_requests") -> Optional[str]:
        """
        Send a message via MCP protocol for LLM processing.
        
        Args:
            message: The message to send
            channel: MCP channel to use
            
        Returns:
            Response from the LLM via MCP
        """
        if not self.mcp_protocol:
            # Fallback to direct API call if no MCP protocol
            return await self.simple_completion(message)
        
        try:
            # Create MCP message for LLM request
            mcp_message = MCPMessage(
                channel=channel,
                data={
                    "prompt": message,
                    "model": self.config.default_model,
                    "max_tokens": self.config.max_tokens,
                    "temperature": self.config.temperature
                },
                message_type="llm_request",
                message_id=f"llm_req_{int(time.time() * 1000)}"
            )
            
            # Send via MCP protocol
            await self.mcp_protocol.send_message(
                channel=mcp_message.channel,
                data=mcp_message.data,
                message_type=mcp_message.message_type
            )
            
            # For now, also make direct API call as fallback
            # In a full MCP implementation, we'd wait for MCP response
            return await self.simple_completion(message)
            
        except Exception as e:
            print(f"Error sending MCP message: {e}")
            # Fallback to direct API call
            return await self.simple_completion(message)
    
    async def chat_completion_with_mcp(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        channel: str = "llm_requests",
        **kwargs
    ) -> ChatResponse:
        """
        Chat completion with MCP protocol integration.
        
        Args:
            messages: Chat messages
            model: Model to use
            channel: MCP channel
            **kwargs: Additional parameters
            
        Returns:
            Chat response
        """
        if not self.mcp_protocol:
            # Fallback to direct API call
            return await self.chat_completion(messages, model, **kwargs)
        
        try:
            # Create MCP message for chat request
            mcp_message = MCPMessage(
                channel=channel,
                data={
                    "messages": [msg.dict() for msg in messages],
                    "model": model or self.config.default_model,
                    **kwargs
                },
                message_type="chat_request",
                message_id=f"chat_req_{int(time.time() * 1000)}"
            )
            
            # Send via MCP protocol
            await self.mcp_protocol.send_message(
                channel=mcp_message.channel,
                data=mcp_message.data,
                message_type=mcp_message.message_type
            )
            
            # For now, also make direct API call as fallback
            # In a full MCP implementation, we'd wait for MCP response
            return await self.chat_completion(messages, model, **kwargs)
            
        except Exception as e:
            print(f"Error sending MCP chat message: {e}")
            # Fallback to direct API call
            return await self.chat_completion(messages, model, **kwargs)
    
    def convert_mcp_tool_format(self, tool_definition: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert MCP tool definition to OpenAI-compatible format.
        Based on OpenRouter's MCP server documentation.
        
        Args:
            tool_definition: MCP tool definition
            
        Returns:
            OpenAI-compatible tool definition
        """
        return {
            "type": "function",
            "function": {
                "name": tool_definition.get("name", ""),
                "description": tool_definition.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": tool_definition.get("inputSchema", {}).get("properties", {}),
                    "required": tool_definition.get("inputSchema", {}).get("required", [])
                }
            }
        }


class LLMCamperMixin:
    """
    Mixin class to add LLM capabilities to Campers.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.llm_client: Optional[OpenRouterClient] = None
        self._llm_config: Optional[OpenRouterConfig] = None
    
    def setup_llm(self, config: OpenRouterConfig = None, mcp_protocol: MCPProtocol = None) -> None:
        """
        Setup LLM client with optional MCP protocol support.
        
        Args:
            config: OpenRouter configuration
            mcp_protocol: Optional MCP protocol for inter-camper communication
        """
        self._llm_config = config
        # Pass MCP protocol if available (e.g., from parent Camper)
        if mcp_protocol is None and hasattr(self, 'mcp_protocol'):
            mcp_protocol = self.mcp_protocol
        self.llm_client = OpenRouterClient(config, mcp_protocol=mcp_protocol)
    
    async def llm_completion(
        self, 
        prompt: str, 
        system_prompt: str = None,
        model: str = None,
        **kwargs
    ) -> str:
        """
        Get LLM completion.
        
        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            model: Model to use
            **kwargs: Additional parameters
            
        Returns:
            Completion text
        """
        if not self.llm_client:
            self.setup_llm()
        
        async with self.llm_client:
            return await self.llm_client.simple_completion(
                prompt, model, system_prompt, **kwargs
            )
    
    async def llm_chat(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        **kwargs
    ) -> ChatResponse:
        """
        Get LLM chat completion.
        
        Args:
            messages: Chat messages
            model: Model to use
            **kwargs: Additional parameters
            
        Returns:
            Chat response
        """
        if not self.llm_client:
            self.setup_llm()
        
        async with self.llm_client:
            return await self.llm_client.chat_completion(messages, model, **kwargs)
    
    async def llm_stream(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        **kwargs
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Get streaming LLM completion.
        
        Args:
            messages: Chat messages
            model: Model to use
            **kwargs: Additional parameters
            
        Yields:
            Streaming response chunks
        """
        if not self.llm_client:
            self.setup_llm()
        
        async with self.llm_client:
            async for chunk in self.llm_client.stream_chat_completion(messages, model, **kwargs):
                yield chunk
    
    async def llm_completion_with_mcp(
        self, 
        prompt: str, 
        channel: str = "llm_requests",
        **kwargs
    ) -> str:
        """
        Get LLM completion with MCP protocol integration.
        
        Args:
            prompt: User prompt
            channel: MCP channel to use
            **kwargs: Additional parameters
            
        Returns:
            Completion text
        """
        if not self.llm_client:
            self.setup_llm()
        
        async with self.llm_client:
            return await self.llm_client.send_mcp_message(prompt, channel)
    
    async def llm_chat_with_mcp(
        self, 
        messages: List[ChatMessage], 
        model: str = None,
        channel: str = "llm_requests",
        **kwargs
    ) -> ChatResponse:
        """
        Get LLM chat completion with MCP protocol integration.
        
        Args:
            messages: Chat messages
            model: Model to use
            channel: MCP channel
            **kwargs: Additional parameters
            
        Returns:
            Chat response
        """
        if not self.llm_client:
            self.setup_llm()
        
        async with self.llm_client:
            return await self.llm_client.chat_completion_with_mcp(messages, model, channel, **kwargs)


# Convenience functions
async def quick_completion(prompt: str, api_key: str = None, model: str = None) -> str:
    """
    Quick completion function for simple use cases.
    
    Args:
        prompt: User prompt
        api_key: OpenRouter API key (uses env var if not provided)
        model: Model to use
        
    Returns:
        Completion text
    """
    config = OpenRouterConfig(
        api_key=api_key,
        model=model or "openai/gpt-oss-20b:free"
    )
    
    async with OpenRouterClient(config) as client:
        return await client.simple_completion(prompt, model=config.model)


async def quick_chat(messages: List[Dict[str, str]], api_key: str = None, model: str = None) -> str:
    """
    Quick chat function for simple use cases.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content'
        api_key: OpenRouter API key
        model: Model to use
        
    Returns:
        Response text
    """
    config = OpenRouterConfig(
        api_key=api_key,
        model=model or "openai/gpt-oss-20b:free"
    )
    
    chat_messages = [ChatMessage(**msg) for msg in messages]
    
    async with OpenRouterClient(config) as client:
        response = await client.chat_completion(chat_messages, model=config.model)
        if response.choices and len(response.choices) > 0:
            return response.choices[0]['message']['content']
        return ""