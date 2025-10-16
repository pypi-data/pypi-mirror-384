"""
Base image provider interface for LLM Provider Factory
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel


class ImageResponse(BaseModel):
    """Image generation response model"""
    urls: List[str]
    model: str
    prompt: str
    metadata: Optional[Dict[str, Any]] = None


class BaseImageProvider(ABC):
    """Abstract base class for image providers"""
    
    def __init__(self, config):
        self.config = config
    
    @abstractmethod
    async def generate_image(self, prompt: str, **kwargs) -> ImageResponse:
        """Generate image(s) from text prompt"""
        pass
    
    @abstractmethod
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        pass