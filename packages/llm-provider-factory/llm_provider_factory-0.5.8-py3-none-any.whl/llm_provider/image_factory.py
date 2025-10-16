"""
Image Provider Factory for managing multiple image generation providers
"""

import logging
from typing import Dict, Type, Optional, Any
from .base_image_provider import BaseImageProvider
from .utils.config import OpenAIImageConfig, ReplicateImageConfig
from .utils.logger import get_logger

logger = get_logger(__name__)


class ImageProviderFactory:
    """Factory for creating and managing image providers"""
    
    def __init__(self):
        self._providers: Dict[str, Type[BaseImageProvider]] = {}
        self._register_default_providers()
    
    def _register_default_providers(self):
        """Register default image providers"""
        try:
            from .providers.openai_image_provider import OpenAIImageProvider
            self._providers["openai_image"] = OpenAIImageProvider
            logger.info("✅ OpenAI Image provider registered")
        except ImportError as e:
            logger.warning(f"⚠️ OpenAI Image provider not available: {e}")
        
        try:
            from .providers.replicate_image_provider import ReplicateImageProvider
            self._providers["replicate_image"] = ReplicateImageProvider
            logger.info("✅ Replicate Image provider registered")
        except ImportError as e:
            logger.warning(f"⚠️ Replicate Image provider not available: {e}")
    
    def create_provider(self, provider_name: str, config) -> BaseImageProvider:
        """Create an image provider instance"""
        if provider_name not in self._providers:
            available = list(self._providers.keys())
            raise ValueError(f"Unknown image provider: {provider_name}. Available: {available}")
        
        provider_class = self._providers[provider_name]
        return provider_class(config)
    
    def create_openai_image(
        self,
        api_key: str,
        model: str = "dall-e-3",
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid",
        **kwargs
    ) -> BaseImageProvider:
        """Create OpenAI DALL-E image provider"""
        config = OpenAIImageConfig(
            api_key=api_key,
            model=model,
            size=size,
            quality=quality,
            style=style,
            **kwargs
        )
        return self.create_provider("openai_image", config)
    
    def create_replicate_image(
        self,
        api_token: str,
        model: str = "stability-ai/stable-diffusion",
        version: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 50,
        **kwargs
    ) -> BaseImageProvider:
        """Create Replicate image provider"""
        config = ReplicateImageConfig(
            api_key=api_token,  # Map api_token to api_key for config
            model=model,
            version=version,
            width=width,
            height=height,
            steps=steps,
            **kwargs
        )
        return self.create_provider("replicate_image", config)
    
    def list_providers(self) -> Dict[str, Dict[str, Any]]:
        """List all available image providers"""
        providers_info = {}
        
        for name, provider_class in self._providers.items():
            try:
                # Create a dummy config to get provider info
                if name == "openai_image":
                    dummy_config = OpenAIImageConfig(api_key="dummy", model="dall-e-3")
                elif name == "replicate_image":
                    dummy_config = ReplicateImageConfig(api_key="dummy", model="stability-ai/stable-diffusion")
                else:
                    continue
                
                provider = provider_class(dummy_config)
                providers_info[name] = provider.get_provider_info()
            except Exception as e:
                providers_info[name] = {
                    "name": name,
                    "error": str(e),
                    "is_available": False
                }
        
        return providers_info
    
    def get_available_providers(self) -> Dict[str, Type[BaseImageProvider]]:
        """Get available image providers"""
        return self._providers.copy()
    
    def register_provider(self, name: str, provider_class: Type[BaseImageProvider]):
        """Register a custom image provider"""
        if not issubclass(provider_class, BaseImageProvider):
            raise ValueError("Provider must inherit from BaseImageProvider")
        
        self._providers[name] = provider_class
        logger.info(f"✅ Custom image provider registered: {name}")


# Global factory instance
image_factory = ImageProviderFactory()