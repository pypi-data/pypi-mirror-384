"""Anthropic Claude provider implementation."""

from typing import Optional, AsyncIterator, List, Dict, Any
import anthropic
from anthropic import AsyncAnthropic

from ..base_provider import BaseLLMProvider
from ..settings import (
    GenerationRequest, 
    GenerationResponse, 
    StreamChunk, 
    ProviderInfo,
    Message,
    MessageRole
)
from ..utils.config import AnthropicConfig, ProviderConfig
from ..utils.exceptions import (
    InvalidConfigurationError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ModelNotAvailableError,
    GenerationError
)
from ..utils.logger import logger


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider implementation."""
    
    SUPPORTED_MODELS = [
        "claude-3-opus-20240229",
        "claude-3-sonnet-20240229",
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20240620",
        "claude-2.1",
        "claude-2.0",
        "claude-instant-1.2"
    ]
    
    def __init__(self, config: Optional[AnthropicConfig] = None) -> None:
        """Initialize Anthropic provider.
        
        Args:
            config: Anthropic configuration. If None, will try to load from environment.
        """
        if config is None:
            config = AnthropicConfig.from_env()
        
        super().__init__(config)
        self.client: Optional[AsyncAnthropic] = None
        self.config: AnthropicConfig = config
    
    def get_provider_info(self) -> ProviderInfo:
        """Get Anthropic provider information."""
        return ProviderInfo(
            name="anthropic",
            display_name="Anthropic Claude",
            description="Anthropic's Claude models for conversational AI",
            supported_models=self.SUPPORTED_MODELS,
            capabilities=["chat", "completion", "streaming"],
            is_available=self.config.api_key is not None
        )
    
    async def initialize(self) -> None:
        """Initialize Anthropic client."""
        if not self.validate_config():
            raise InvalidConfigurationError("Invalid Anthropic configuration", "anthropic")
        
        try:
            self.client = AsyncAnthropic(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
            
            logger.info("Anthropic client initialized successfully", "anthropic")
            
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(f"Anthropic authentication failed: {str(e)}", "anthropic")
        except Exception as e:
            raise APIError(f"Failed to initialize Anthropic client: {str(e)}", "anthropic")
    
    def validate_config(self) -> bool:
        """Validate Anthropic configuration."""
        if not self.config.api_key:
            raise InvalidConfigurationError("Anthropic API key is required", "anthropic")
        
        if self.config.model not in self.SUPPORTED_MODELS:
            raise InvalidConfigurationError(
                f"Model '{self.config.model}' is not supported. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS)}", 
                "anthropic"
            )
        
        return True
    
    def is_available(self) -> bool:
        """Check if Anthropic provider is available."""
        return bool(self.config.api_key)
    
    def get_supported_models(self) -> List[str]:
        """Get supported Anthropic models."""
        return self.SUPPORTED_MODELS.copy()
    
    def _convert_messages(self, request: GenerationRequest) -> tuple[Optional[str], List[Dict[str, str]]]:
        """Convert request to Anthropic message format.
        
        Returns:
            Tuple of (system_message, messages)
        """
        system_message = None
        messages = []
        
        # Process conversation history
        if request.history:
            for msg in request.history:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
        
        # Add current prompt as user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return system_message, messages
    
    def _parse_finish_reason(self, stop_reason: Optional[str]) -> Optional[str]:
        """Parse Anthropic stop reason."""
        if not stop_reason:
            return None
        
        reason_map = {
            "end_turn": "stop",
            "max_tokens": "max_tokens",
            "stop_sequence": "stop_sequence",
            "tool_use": "tool_use"
        }
        
        return reason_map.get(stop_reason, stop_reason)
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Anthropic API."""
        await self.ensure_initialized()
        
        try:
            system_message, messages = self._convert_messages(request)
            
            # Prepare request parameters
            params = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": False
            }
            
            # Add system message if present
            if system_message:
                params["system"] = system_message
            
            # Add optional parameters
            if request.top_p is not None:
                params["top_p"] = request.top_p
            
            if request.stop_sequences:
                params["stop_sequences"] = request.stop_sequences
            
            logger.debug(f"Making Anthropic API call with model: {self.config.model}", "anthropic")
            
            response = await self.client.messages.create(**params)
            
            # Extract content from response
            content = ""
            if response.content:
                for block in response.content:
                    if hasattr(block, 'text'):
                        content += block.text
            
            return GenerationResponse(
                content=content,
                finish_reason=self._parse_finish_reason(response.stop_reason),
                usage={
                    "input_tokens": response.usage.input_tokens if response.usage else 0,
                    "output_tokens": response.usage.output_tokens if response.usage else 0,
                    "total_tokens": (response.usage.input_tokens + response.usage.output_tokens) if response.usage else 0,
                } if response.usage else None,
                provider="anthropic",
                model=self.config.model,
                metadata={
                    "response_id": response.id,
                    "model": response.model,
                    "role": response.role,
                    "type": response.type
                }
            )
            
        except anthropic.RateLimitError as e:
            raise RateLimitError(f"Anthropic rate limit exceeded: {str(e)}", "anthropic")
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(f"Anthropic authentication error: {str(e)}", "anthropic")
        except anthropic.NotFoundError as e:
            raise ModelNotAvailableError(f"Anthropic model not found: {str(e)}", self.config.model, "anthropic")
        except anthropic.APIError as e:
            raise APIError(f"Anthropic API error: {str(e)}", "anthropic", getattr(e, 'status_code', None))
        except Exception as e:
            raise GenerationError(f"Anthropic generation failed: {str(e)}", "anthropic")
    
    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[StreamChunk]:
        """Generate text with streaming using Anthropic API."""
        await self.ensure_initialized()
        
        try:
            system_message, messages = self._convert_messages(request)
            
            # Prepare request parameters
            params = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": True
            }
            
            # Add system message if present
            if system_message:
                params["system"] = system_message
            
            # Add optional parameters
            if request.top_p is not None:
                params["top_p"] = request.top_p
            
            if request.stop_sequences:
                params["stop_sequences"] = request.stop_sequences
            
            logger.debug(f"Starting Anthropic streaming with model: {self.config.model}", "anthropic")
            
            async with self.client.messages.stream(**params) as stream:
                async for event in stream:
                    if event.type == "content_block_delta":
                        if hasattr(event.delta, 'text') and event.delta.text:
                            yield StreamChunk(
                                content=event.delta.text,
                                is_final=False,
                                metadata={
                                    "event_type": event.type,
                                    "index": event.index
                                }
                            )
                    
                    elif event.type == "message_stop":
                        yield StreamChunk(
                            content="",
                            is_final=True,
                            finish_reason=self._parse_finish_reason(getattr(event, 'stop_reason', None))
                        )
                        break
            
        except anthropic.RateLimitError as e:
            raise RateLimitError(f"Anthropic rate limit exceeded: {str(e)}", "anthropic")
        except anthropic.AuthenticationError as e:
            raise AuthenticationError(f"Anthropic authentication error: {str(e)}", "anthropic")
        except anthropic.NotFoundError as e:
            raise ModelNotAvailableError(f"Anthropic model not found: {str(e)}", self.config.model, "anthropic")
        except anthropic.APIError as e:
            raise APIError(f"Anthropic API error: {str(e)}", "anthropic", getattr(e, 'status_code', None))
        except Exception as e:
            raise GenerationError(f"Anthropic streaming failed: {str(e)}", "anthropic")