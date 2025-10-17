"""
OpenAI DALL-E Image Provider
"""

import logging
from typing import Dict, Any, Optional
import httpx
from ..base_image_provider import BaseImageProvider, ImageResponse
from ..utils.config import OpenAIImageConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("⚠️ OpenAI package not available")


class OpenAIImageProvider(BaseImageProvider):
    """OpenAI DALL-E image generation provider"""
    
    def __init__(self, config: OpenAIImageConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.size = config.size
        self.quality = config.quality
        self.style = config.style
        self.n = config.n
        self.timeout = config.timeout
        
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package is required for OpenAI image provider")
        
        # Initialize OpenAI client
        self.client = openai.AsyncOpenAI(
            api_key=self.api_key,
            timeout=self.timeout
        )
        
        logger.info(f"🎨 OpenAI Image Provider initialized: model={self.model}")
    
    async def generate_image(self, prompt: str, **kwargs) -> ImageResponse:
        """Generate image using OpenAI DALL-E"""
        try:
            # Override config with kwargs if provided
            model = kwargs.get("model", self.model)
            size = kwargs.get("size", self.size)
            quality = kwargs.get("quality", self.quality)
            style = kwargs.get("style", self.style)
            n = kwargs.get("n", self.n)
            
            logger.info(f"🎨 Generating image with OpenAI: prompt='{prompt[:50]}...', model={model}")
            
            # Call OpenAI API
            response = await self.client.images.generate(
                model=model,
                prompt=prompt,
                size=size,
                quality=quality,
                style=style,
                n=n
            )
            
            # Extract URLs from response
            urls = []
            for image in response.data:
                if hasattr(image, 'url') and image.url:
                    urls.append(image.url)
                elif hasattr(image, 'b64_json') and image.b64_json:
                    # Convert base64 to data URL if needed
                    urls.append(f"data:image/png;base64,{image.b64_json}")
            
            if not urls:
                raise ValueError("No image URLs received from OpenAI")
            
            logger.info(f"✅ OpenAI image generation successful: {len(urls)} images")
            
            return ImageResponse(
                urls=urls,
                model=model,
                prompt=prompt,
                metadata={
                    "provider": "openai",
                    "size": size,
                    "quality": quality,
                    "style": style,
                    "n": n
                }
            )
            
        except Exception as e:
            logger.error(f"❌ OpenAI image generation failed: {e}")
            raise Exception(f"OpenAI image generation error: {str(e)}")
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "name": "openai_image",
            "display_name": "OpenAI DALL-E",
            "type": "image",
            "supported_models": ["dall-e-2", "dall-e-3"],
            "supported_sizes": ["256x256", "512x512", "1024x1024", "1024x1792", "1792x1024"],
            "supported_qualities": ["standard", "hd"],
            "supported_styles": ["vivid", "natural"],
            "capabilities": ["text-to-image"],
            "is_available": OPENAI_AVAILABLE and bool(self.api_key)
        }