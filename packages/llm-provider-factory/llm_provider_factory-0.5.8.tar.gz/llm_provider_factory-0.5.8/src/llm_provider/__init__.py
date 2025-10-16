"""
LLM Provider Factory - A unified interface for multiple LLM providers.

This package provides a clean, extensible way to interact with different LLM providers
(OpenAI, Anthropic, Gemini, etc.) through a single, consistent interface.

Example usage:
    ```python
    from llm_provider import LLMProviderFactory, OpenAI
    
    # Method 1: Using factory with provider instance
    provider = LLMProviderFactory(OpenAI())
    response = await provider.generate("Hello, world!")
    
    # Method 2: Using factory with provider name
    factory = LLMProviderFactory()
    factory.set_provider("openai")
    response = await factory.generate("Hello, world!")
    
    # Method 3: Direct provider usage
    factory = LLMProviderFactory.create_openai()
    response = await factory.generate("Hello, world!")
    ```

Image generation example:
    ```python
    from llm_provider import ImageProviderFactory
    
    # Create image factory
    factory = ImageProviderFactory()
    
    # Generate image with OpenAI DALL-E
    provider = factory.create_openai_image(api_key="your-key")
    response = await provider.generate_image("A beautiful sunset")
    print(response.urls[0])  # Image URL
    ```
"""

from .factory import LLMProviderFactory
from .base_provider import BaseLLMProvider

# Image support
try:
    from .image_factory import ImageProviderFactory
    from .base_image_provider import BaseImageProvider, ImageResponse
    IMAGE_SUPPORT = True
except ImportError as e:
    print(f"Image support import error: {e}")
    ImageProviderFactory = None
    BaseImageProvider = None
    ImageResponse = None
    IMAGE_SUPPORT = False

from .providers import (
    OpenAIProvider,
    AnthropicProvider,
    GeminiProvider,
    OpenAI,
    Anthropic,
    Gemini,
)
from .settings import (
    GenerationRequest,
    GenerationResponse,
    StreamChunk,
    Message,
    MessageRole,
    ProviderInfo,
)
from .utils import (
    # Configurations
    ProviderConfig,
    OpenAIConfig,
    AnthropicConfig,
    GeminiConfig,
    ConfigManager,
    config_manager,
    # Exceptions
    LLMProviderError,
    ProviderNotFoundError,
    InvalidConfigurationError,
    APIError,
    RateLimitError,
    AuthenticationError,
    ModelNotAvailableError,
    GenerationError,
    # Logger
    logger,
)

__version__ = "0.5.8"
__author__ = "Sadık Hanecioglu"
__email__ = "sadik@example.com"

__all__ = [
    # Main factory
    "LLMProviderFactory",
    
    # Base classes
    "BaseLLMProvider",
    
    # Providers
    "OpenAIProvider",
    "AnthropicProvider", 
    "GeminiProvider",
    "OpenAI",
    "Anthropic",
    "Gemini",
    
    # Data models
    "GenerationRequest",
    "GenerationResponse",
    "StreamChunk",
    "Message",
    "MessageRole",
    "ProviderInfo",
    
    # Configurations
    "ProviderConfig",
    "OpenAIConfig",
    "AnthropicConfig",
    "GeminiConfig",
    "ConfigManager",
    "config_manager",
    
    # Exceptions
    "LLMProviderError",
    "ProviderNotFoundError",
    "InvalidConfigurationError",
    "APIError",
    "RateLimitError",
    "AuthenticationError",
    "ModelNotAvailableError",
    "GenerationError",
    
    # Utilities
    "logger",
]

# Add image support to __all__ if available
if IMAGE_SUPPORT:
    __all__.extend([
        "ImageProviderFactory",
        "BaseImageProvider", 
        "ImageResponse",
    ])