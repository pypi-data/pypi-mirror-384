"""Ollama provider implementation."""

from typing import Optional, AsyncIterator, List, Dict, Any
import httpx
import json

from ..base_provider import BaseLLMProvider
from ..settings import (
    GenerationRequest, 
    GenerationResponse, 
    StreamChunk, 
    ProviderInfo,
    Message,
    MessageRole
)
from ..utils.config import ProviderConfig, OllamaConfig
from ..utils.exceptions import (
    InvalidConfigurationError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ModelNotAvailableError,
    GenerationError
)
from ..utils.logger import logger


class OllamaProvider(BaseLLMProvider):
    """Ollama LLM provider for local models."""
    
    SUPPORTED_MODELS = [
        "llama2",
        "llama2:7b",
        "llama2:13b",
        "llama2:70b",
        "codellama",
        "codellama:7b",
        "codellama:13b",
        "codellama:34b",
        "mistral",
        "mistral:7b",
        "neural-chat",
        "starling-lm",
        "openchat",
        "wizard-vicuna-uncensored",
        "phind-codellama",
        "dolphin-mixtral"
    ]
    
    def __init__(self, config: Optional[OllamaConfig] = None) -> None:
        """Initialize Ollama provider."""
        if config is None:
            config = OllamaConfig.from_env()
        
        super().__init__(config)
        self.config: OllamaConfig = config
        self.provider_name = "ollama"
        self.base_url = config.base_url
        self.model_name = config.model
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout
        
        logger.info(f"🦙 Ollama Provider oluşturuldu: model={self.model_name}, base_url={self.base_url}")
    
    async def initialize(self) -> None:
        """Initialize Ollama connection."""
        try:
            # Test connection to Ollama server
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/api/tags",
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    models = response.json()
                    available_models = [model['name'] for model in models.get('models', [])]
                    logger.info(f"✅ Ollama bağlantısı başarılı. Mevcut modeller: {len(available_models)} adet")
                    
                    # Check if requested model is available
                    if available_models and self.model_name not in available_models:
                        logger.warning(f"⚠️ Model '{self.model_name}' bulunamadı. Mevcut modeller: {available_models}")
                else:
                    raise APIError(f"Ollama server response: {response.status_code}", "ollama")
                    
        except httpx.ConnectError:
            raise InvalidConfigurationError(
                f"Ollama server'a bağlanılamadı: {self.base_url}. "
                "Ollama'nın çalıştığından emin olun: ollama serve", 
                "ollama"
            )
        except Exception as e:
            logger.error(f"Ollama initialization failed: {e}")
            raise InvalidConfigurationError(f"Ollama başlatılamadı: {str(e)}", "ollama")
    
    def validate_config(self) -> bool:
        """Validate Ollama configuration."""
        if not self.config.base_url:
            raise InvalidConfigurationError("Ollama base URL gereklidir", "ollama")
        
        if not self.config.model:
            raise InvalidConfigurationError("Ollama model gereklidir", "ollama")
        
        return True
    
    def is_available(self) -> bool:
        """Check if Ollama is available."""
        return bool(self.config.base_url and self.config.model)
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response using Ollama.
        
        Args:
            request: The generation request
            
        Returns:
            Generated response
            
        Raises:
            GenerationError: If generation fails
        """
        try:
            await self.ensure_initialized()
            
            # Convert history to Ollama format if provided
            messages = []
            if request.history:
                for msg in request.history:
                    role = str(msg.role) if hasattr(msg.role, 'value') else str(msg.role)
                    if role == "assistant":
                        role = "assistant"
                    elif role == "system":
                        role = "system"
                    else:
                        role = "user"
                        
                    messages.append({
                        "role": role,
                        "content": msg.content
                    })
            
            # Add current prompt
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False,
                "options": {
                    "temperature": request.temperature or self.temperature,
                    "num_predict": request.max_tokens or self.max_tokens,
                }
            }
            
            logger.info(f"Ollama API çağrısı yapılıyor: {self.base_url}/api/chat")
            
            # Make HTTP request
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                )
                
            logger.info(f"Ollama API response status: {response.status_code}")
                
            if response.status_code != 200:
                logger.error(f"Ollama API error response: {response.text}")
                raise APIError(f"Ollama API error: {response.status_code} - {response.text}", "ollama")
                
            result = response.json()
            
            if "message" in result and "content" in result["message"]:
                content = result["message"]["content"]
                
                # Calculate token usage (rough estimate)
                prompt_tokens = len(request.prompt.split())
                completion_tokens = len(content.split())
                
                return GenerationResponse(
                    content=content,
                    provider=self.provider_name,
                    model=self.model_name,
                    usage={
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": prompt_tokens + completion_tokens
                    }
                )
            else:
                logger.error(f"Unexpected Ollama response format: {result}")
                raise GenerationError("Ollama API response format unexpected", "ollama")
                
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise GenerationError(f"Ollama generation failed: {str(e)}", "ollama")

    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response using Ollama.
        
        Args:
            request: The generation request
            
        Yields:
            Stream chunks of the response
            
        Raises:
            GenerationError: If generation fails
        """
        try:
            await self.ensure_initialized()
            
            # Convert history to Ollama format if provided
            messages = []
            if request.history:
                for msg in request.history:
                    role = str(msg.role) if hasattr(msg.role, 'value') else str(msg.role)
                    if role == "assistant":
                        role = "assistant"
                    elif role == "system":
                        role = "system"
                    else:
                        role = "user"
                        
                    messages.append({
                        "role": role,
                        "content": msg.content
                    })
            
            # Add current prompt
            messages.append({
                "role": "user",
                "content": request.prompt
            })
            
            # Prepare request payload
            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": True,
                "options": {
                    "temperature": request.temperature or self.temperature,
                    "num_predict": request.max_tokens or self.max_tokens,
                }
            }
            
            logger.info(f"Ollama streaming API çağrısı yapılıyor: {self.base_url}/api/chat")
            
            # Make streaming HTTP request
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/api/chat",
                    json=payload,
                    timeout=self.timeout
                ) as response:
                    
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(f"Ollama streaming API error: {error_text}")
                        raise APIError(f"Ollama streaming API error: {response.status_code} - {error_text}", "ollama")
                    
                    async for line in response.aiter_lines():
                        if line.strip():
                            try:
                                chunk_data = json.loads(line)
                                
                                if "message" in chunk_data and "content" in chunk_data["message"]:
                                    content = chunk_data["message"]["content"]
                                    
                                    yield StreamChunk(
                                        content=content,
                                        model=self.model_name,
                                        finish_reason="partial" if not chunk_data.get("done", False) else "complete"
                                    )
                                    
                                if chunk_data.get("done", False):
                                    break
                                    
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse Ollama stream chunk: {line}")
                                continue
                                
        except Exception as e:
            logger.error(f"Ollama streaming generation failed: {e}")
            raise GenerationError(f"Ollama streaming generation failed: {str(e)}", "ollama")

    def get_provider_info(self) -> ProviderInfo:
        """Get provider information."""
        return ProviderInfo(
            name="ollama",
            display_name="Ollama",
            description="Ollama provider for running local LLMs",
            supported_models=self.SUPPORTED_MODELS,
            capabilities=["text_generation", "conversation", "streaming", "system_messages"],
            is_available=self.is_available()
        )