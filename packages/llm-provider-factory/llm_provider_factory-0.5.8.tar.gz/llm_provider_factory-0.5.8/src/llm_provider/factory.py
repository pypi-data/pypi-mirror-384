"""LLM Provider Factory - Main factory class for managing LLM providers."""

from typing import Dict, Type, Optional, List, Union, AsyncIterator
from .base_provider import BaseLLMProvider
from .providers import OpenAIProvider, AnthropicProvider, GeminiProvider, VertexAIProvider, OllamaProvider
from .settings import GenerationRequest, GenerationResponse, StreamChunk, ProviderInfo, Message
from .utils.exceptions import ProviderNotFoundError, InvalidConfigurationError
from .utils.logger import logger
from .utils.config import ProviderConfig, OpenAIConfig, AnthropicConfig, GeminiConfig, VertexAIConfig, OllamaConfig


class LLMProviderFactory:
    """Factory class for managing and using different LLM providers."""
    
    def __init__(self, provider: Optional[BaseLLMProvider] = None) -> None:
        """Initialize the factory with an optional provider.
        
        Args:
            provider: Optional provider instance to use directly
        """
        self._providers: Dict[str, Type[BaseLLMProvider]] = {
            "openai": OpenAIProvider,
            "anthropic": AnthropicProvider,
            "gemini": GeminiProvider,
            "vertexai": VertexAIProvider,
            "ollama": OllamaProvider,
        }
        
        self._current_provider: Optional[BaseLLMProvider] = provider
        self._provider_instances: Dict[str, BaseLLMProvider] = {}
        
        if provider:
            logger.info(f"Factory initialized with provider: {provider.provider_name}")
        else:
            logger.info("Factory initialized without default provider")
    
    def register_provider(self, name: str, provider_class: Type[BaseLLMProvider]) -> None:
        """Register a new provider class.
        
        Args:
            name: Provider name
            provider_class: Provider class that extends BaseLLMProvider
        """
        self._providers[name.lower()] = provider_class
        logger.info(f"Registered new provider: {name}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available provider names.
        
        Returns:
            List of provider names
        """
        return list(self._providers.keys())
    
    def get_provider_info(self, provider_name: Optional[str] = None) -> Union[ProviderInfo, List[ProviderInfo]]:
        """Get information about a provider or all providers.
        
        Args:
            provider_name: Optional provider name. If None, returns info for all providers.
            
        Returns:
            ProviderInfo for specific provider or list of ProviderInfo for all providers
        """
        if provider_name:
            provider = self._get_provider_instance(provider_name)
            return provider.get_provider_info()
        else:
            # Return info for all providers
            info_list = []
            for name in self._providers.keys():
                try:
                    provider = self._get_provider_instance(name)
                    info_list.append(provider.get_provider_info())
                except Exception as e:
                    logger.warning(f"Could not get info for provider {name}: {e}")
            return info_list
    
    def create_provider(self, provider_name: str, config: Optional[ProviderConfig] = None) -> BaseLLMProvider:
        """Create a new provider instance.
        
        Args:
            provider_name: Name of the provider to create
            config: Optional configuration for the provider
            
        Returns:
            Provider instance
            
        Raises:
            ProviderNotFoundError: If provider is not found
        """
        provider_name = provider_name.lower()
        
        if provider_name not in self._providers:
            available = ", ".join(self._providers.keys())
            raise ProviderNotFoundError(
                f"Provider '{provider_name}' not found. Available providers: {available}",
                provider_name
            )
        
        provider_class = self._providers[provider_name]
        return provider_class(config)
    
    def _get_provider_instance(self, provider_name: str) -> BaseLLMProvider:
        """Get or create a provider instance.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider instance
        """
        provider_name = provider_name.lower()
        
        if provider_name not in self._provider_instances:
            self._provider_instances[provider_name] = self.create_provider(provider_name)
        
        return self._provider_instances[provider_name]
    
    def set_provider(self, provider: Union[str, BaseLLMProvider], config: Optional[ProviderConfig] = None) -> None:
        """Set the current provider.
        
        Args:
            provider: Provider name or provider instance
            config: Optional configuration (only used if provider is a string)
        """
        if isinstance(provider, str):
            self._current_provider = self.create_provider(provider, config)
        else:
            self._current_provider = provider
        
        logger.info(f"Current provider set to: {self._current_provider.provider_name}")
    
    def get_current_provider(self) -> Optional[BaseLLMProvider]:
        """Get the current provider.
        
        Returns:
            Current provider instance or None
        """
        return self._current_provider
    
    async def generate(
        self, 
        prompt: str, 
        history: Optional[List[Message]] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> GenerationResponse:
        """Generate text using the specified or current provider.
        
        Args:
            prompt: The prompt for generation
            history: Optional conversation history
            provider: Optional provider name. If None, uses current provider.
            **kwargs: Additional generation parameters
            
        Returns:
            GenerationResponse with generated content
            
        Raises:
            InvalidConfigurationError: If no provider is set
        """
        # Determine which provider to use
        if provider:
            provider_instance = self._get_provider_instance(provider)
        elif self._current_provider:
            provider_instance = self._current_provider
        else:
            raise InvalidConfigurationError("No provider set. Use set_provider() or specify provider parameter.")
        
        # Create generation request
        request = GenerationRequest(
            prompt=prompt,
            history=history,
            **kwargs
        )
        
        logger.debug(f"Generating text with provider: {provider_instance.provider_name}")
        return await provider_instance.generate(request)
    
    async def stream_generate(
        self, 
        prompt: str, 
        history: Optional[List[Message]] = None,
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncIterator[StreamChunk]:
        """Generate text with streaming using the specified or current provider.
        
        Args:
            prompt: The prompt for generation
            history: Optional conversation history
            provider: Optional provider name. If None, uses current provider.
            **kwargs: Additional generation parameters
            
        Yields:
            StreamChunk objects with partial content
            
        Raises:
            InvalidConfigurationError: If no provider is set
        """
        # Determine which provider to use
        if provider:
            provider_instance = self._get_provider_instance(provider)
        elif self._current_provider:
            provider_instance = self._current_provider
        else:
            raise InvalidConfigurationError("No provider set. Use set_provider() or specify provider parameter.")
        
        # Create generation request
        request = GenerationRequest(
            prompt=prompt,
            history=history,
            stream=True,
            **kwargs
        )
        
        logger.debug(f"Starting streaming generation with provider: {provider_instance.provider_name}")
        async for chunk in provider_instance.stream_generate(request):
            yield chunk
    
    # Convenience methods for quick provider creation
    @classmethod
    def create_openai(cls, config: Optional[OpenAIConfig] = None) -> "LLMProviderFactory":
        """Create factory with OpenAI provider.
        
        Args:
            config: Optional OpenAI configuration
            
        Returns:
            Factory instance with OpenAI provider set
        """
        provider = OpenAIProvider(config)
        return cls(provider)
    
    @classmethod
    def create_anthropic(cls, config: Optional[AnthropicConfig] = None) -> "LLMProviderFactory":
        """Create factory with Anthropic provider.
        
        Args:
            config: Optional Anthropic configuration
            
        Returns:
            Factory instance with Anthropic provider set
        """
        provider = AnthropicProvider(config)
        return cls(provider)
    
    @classmethod
    def create_gemini(cls, config: Optional[GeminiConfig] = None) -> "LLMProviderFactory":
        """Create factory with Gemini provider.
        
        Args:
            config: Optional Gemini configuration
            
        Returns:
            Factory instance with Gemini provider set
        """
        provider = GeminiProvider(config)
        return cls(provider)
    
    @classmethod
    def create_vertexai(cls, config: Optional[VertexAIConfig] = None) -> "LLMProviderFactory":
        """Create factory with Vertex AI provider.
        
        Args:
            config: Optional Vertex AI configuration
            
        Returns:
            Factory instance with Vertex AI provider set
        """
        provider = VertexAIProvider(config)
        return cls(provider)
    
    @classmethod
    def create_ollama(cls, config: Optional[OllamaConfig] = None) -> "LLMProviderFactory":
        """Create factory with Ollama provider.
        
        Args:
            config: Optional Ollama configuration
            
        Returns:
            Factory instance with Ollama provider set
        """
        provider = OllamaProvider(config)
        return cls(provider)
    
    def __str__(self) -> str:
        """String representation of the factory."""
        current = self._current_provider.provider_name if self._current_provider else "None"
        return f"LLMProviderFactory(current_provider={current}, available_providers={list(self._providers.keys())})"
    
    def __repr__(self) -> str:
        """Detailed string representation of the factory."""
        return (
            f"LLMProviderFactory("
            f"current_provider={self._current_provider}, "
            f"available_providers={list(self._providers.keys())}, "
            f"provider_instances={list(self._provider_instances.keys())})"
        )