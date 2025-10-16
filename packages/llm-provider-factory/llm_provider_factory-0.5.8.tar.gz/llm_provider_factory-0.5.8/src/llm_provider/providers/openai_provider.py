"""OpenAI provider implementation."""

from typing import Optional, AsyncIterator, List, Dict, Any
import openai
from openai import AsyncOpenAI

from ..base_provider import BaseLLMProvider
from ..settings import (
    GenerationRequest, 
    GenerationResponse, 
    StreamChunk, 
    ProviderInfo,
    Message,
    MessageRole
)
from ..utils.config import OpenAIConfig, ProviderConfig
from ..utils.exceptions import (
    InvalidConfigurationError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ModelNotAvailableError,
    GenerationError
)
from ..utils.logger import logger


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider implementation."""
    
    SUPPORTED_MODELS = [
        "gpt-4",
        "gpt-4-turbo",
        "gpt-4-turbo-preview",
        "gpt-3.5-turbo",
        "gpt-3.5-turbo-16k",
        "gpt-4o",
        "gpt-4o-mini"
    ]
    
    def __init__(self, config: Optional[OpenAIConfig] = None) -> None:
        """Initialize OpenAI provider.
        
        Args:
            config: OpenAI configuration. If None, will try to load from environment.
        """
        if config is None:
            config = OpenAIConfig.from_env()
        
        super().__init__(config)
        self.client: Optional[AsyncOpenAI] = None
        self.config: OpenAIConfig = config
    
    def get_provider_info(self) -> ProviderInfo:
        """Get OpenAI provider information."""
        return ProviderInfo(
            name="openai",
            display_name="OpenAI",
            description="OpenAI GPT models including GPT-4 and GPT-3.5-turbo",
            supported_models=self.SUPPORTED_MODELS,
            capabilities=["chat", "completion", "streaming"],
            is_available=self.config.api_key is not None
        )
    
    async def initialize(self) -> None:
        """Initialize OpenAI client."""
        if not self.validate_config():
            raise InvalidConfigurationError("Invalid OpenAI configuration", "openai")
        
        try:
            self.client = AsyncOpenAI(
                api_key=self.config.api_key,
                organization=self.config.organization,
                base_url=self.config.base_url,
                timeout=self.config.timeout
            )
            
            # Test the connection
            await self.client.models.list()
            logger.info("OpenAI client initialized successfully", "openai")
            
        except openai.AuthenticationError as e:
            raise AuthenticationError(f"OpenAI authentication failed: {str(e)}", "openai")
        except Exception as e:
            raise APIError(f"Failed to initialize OpenAI client: {str(e)}", "openai")
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration."""
        if not self.config.api_key:
            raise InvalidConfigurationError("OpenAI API key is required", "openai")
        
        if self.config.model not in self.SUPPORTED_MODELS:
            raise InvalidConfigurationError(
                f"Model '{self.config.model}' is not supported. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS)}", 
                "openai"
            )
        
        return True
    
    def is_available(self) -> bool:
        """Check if OpenAI provider is available."""
        return bool(self.config.api_key)
    
    def get_supported_models(self) -> List[str]:
        """Get supported OpenAI models."""
        return self.SUPPORTED_MODELS.copy()
    
    def _convert_messages(self, request: GenerationRequest) -> List[Dict[str, str]]:
        """Convert request to OpenAI message format."""
        messages = []
        
        # Add conversation history
        if request.history:
            for msg in request.history:
                messages.append({
                    "role": msg.role.value,
                    "content": msg.content
                })
        
        # Add current prompt as user message
        messages.append({
            "role": "user",
            "content": request.prompt
        })
        
        return messages
    
    def _parse_finish_reason(self, finish_reason: Optional[str]) -> Optional[str]:
        """Parse OpenAI finish reason."""
        if not finish_reason:
            return None
        
        reason_map = {
            "stop": "stop",
            "length": "max_tokens",
            "content_filter": "content_filter",
            "function_call": "function_call",
            "tool_calls": "tool_calls"
        }
        
        return reason_map.get(finish_reason, finish_reason)
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using OpenAI API."""
        await self.ensure_initialized()
        
        try:
            messages = self._convert_messages(request)
            
            # Prepare request parameters
            params = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": False
            }
            
            # Add optional parameters
            if request.top_p is not None:
                params["top_p"] = request.top_p
            
            if request.stop_sequences:
                params["stop"] = request.stop_sequences
            
            logger.debug(f"Making OpenAI API call with model: {self.config.model}", "openai")
            
            response = await self.client.chat.completions.create(**params)
            
            choice = response.choices[0]
            
            return GenerationResponse(
                content=choice.message.content or "",
                finish_reason=self._parse_finish_reason(choice.finish_reason),
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                } if response.usage else None,
                provider="openai",
                model=self.config.model,
                metadata={
                    "response_id": response.id,
                    "created": response.created,
                    "system_fingerprint": response.system_fingerprint
                }
            )
            
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}", "openai")
        except openai.AuthenticationError as e:
            raise AuthenticationError(f"OpenAI authentication error: {str(e)}", "openai")
        except openai.NotFoundError as e:
            raise ModelNotAvailableError(f"OpenAI model not found: {str(e)}", self.config.model, "openai")
        except openai.APIError as e:
            raise APIError(f"OpenAI API error: {str(e)}", "openai", getattr(e, 'status_code', None))
        except Exception as e:
            raise GenerationError(f"OpenAI generation failed: {str(e)}", "openai")
    
    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[StreamChunk]:
        """Generate text with streaming using OpenAI API."""
        await self.ensure_initialized()
        
        try:
            messages = self._convert_messages(request)
            
            # Prepare request parameters
            params = {
                "model": self.config.model,
                "messages": messages,
                "max_tokens": request.max_tokens or self.config.max_tokens,
                "temperature": request.temperature or self.config.temperature,
                "stream": True
            }
            
            # Add optional parameters
            if request.top_p is not None:
                params["top_p"] = request.top_p
            
            if request.stop_sequences:
                params["stop"] = request.stop_sequences
            
            logger.debug(f"Starting OpenAI streaming with model: {self.config.model}", "openai")
            
            stream = await self.client.chat.completions.create(**params)
            
            async for chunk in stream:
                if chunk.choices:
                    choice = chunk.choices[0]
                    delta = choice.delta
                    
                    if delta.content:
                        yield StreamChunk(
                            content=delta.content,
                            is_final=choice.finish_reason is not None,
                            finish_reason=self._parse_finish_reason(choice.finish_reason),
                            metadata={
                                "chunk_id": chunk.id,
                                "created": chunk.created
                            }
                        )
                    
                    # Final chunk
                    if choice.finish_reason:
                        yield StreamChunk(
                            content="",
                            is_final=True,
                            finish_reason=self._parse_finish_reason(choice.finish_reason)
                        )
                        break
            
        except openai.RateLimitError as e:
            raise RateLimitError(f"OpenAI rate limit exceeded: {str(e)}", "openai")
        except openai.AuthenticationError as e:
            raise AuthenticationError(f"OpenAI authentication error: {str(e)}", "openai")
        except openai.NotFoundError as e:
            raise ModelNotAvailableError(f"OpenAI model not found: {str(e)}", self.config.model, "openai")
        except openai.APIError as e:
            raise APIError(f"OpenAI API error: {str(e)}", "openai", getattr(e, 'status_code', None))
        except Exception as e:
            raise GenerationError(f"OpenAI streaming failed: {str(e)}", "openai")