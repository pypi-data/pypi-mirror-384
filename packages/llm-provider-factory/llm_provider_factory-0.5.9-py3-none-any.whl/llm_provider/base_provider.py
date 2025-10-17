"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Optional, AsyncIterator, Any

from .settings import GenerationRequest, GenerationResponse, StreamChunk, ProviderInfo
from .utils.config import ProviderConfig
from .utils.logger import logger


class BaseLLMProvider(ABC):
    """Base class for all LLM providers."""
    
    def __init__(self, config: ProviderConfig) -> None:
        """Initialize the provider with configuration.
        
        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self._initialized = False
    
    async def ensure_initialized(self) -> None:
        """Ensure the provider is initialized."""
        if not self._initialized:
            await self.initialize()
            self._initialized = True
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the provider (e.g., setup client, validate credentials)."""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the provider configuration.
        
        Returns:
            True if configuration is valid
            
        Raises:
            InvalidConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the provider is available for use.
        
        Returns:
            True if provider is available
        """
        pass
    
    @abstractmethod
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate a response to the given request.
        
        Args:
            request: The generation request
            
        Returns:
            Generated response
            
        Raises:
            GenerationError: If generation fails
        """
        pass
    
    @abstractmethod
    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[StreamChunk]:
        """Generate a streaming response to the given request.
        
        Args:
            request: The generation request
            
        Yields:
            Stream chunks of the response
            
        Raises:
            GenerationError: If generation fails
        """
        pass
    
    @abstractmethod
    def get_provider_info(self) -> ProviderInfo:
        """Get information about this provider.
        
        Returns:
            Provider information
        """
        pass
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        return f"{self.__class__.__name__}(config={self.config})"