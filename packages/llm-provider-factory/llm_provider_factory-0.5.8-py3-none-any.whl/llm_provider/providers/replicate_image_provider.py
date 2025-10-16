"""
Replicate Image Provider
"""

import logging
from typing import Dict, Any, Optional, List
import httpx
from ..base_image_provider import BaseImageProvider, ImageResponse
from ..utils.config import ReplicateImageConfig
from ..utils.logger import get_logger

logger = get_logger(__name__)

try:
    import replicate
    REPLICATE_AVAILABLE = True
except ImportError:
    REPLICATE_AVAILABLE = False
    logger.warning("⚠️ Replicate package not available")


class ReplicateImageProvider(BaseImageProvider):
    """Replicate image generation provider"""
    
    def __init__(self, config: ReplicateImageConfig):
        super().__init__(config)
        self.api_key = config.api_key
        self.model = config.model
        self.version = config.version
        self.width = config.width
        self.height = config.height
        self.steps = config.steps
        self.timeout = config.timeout
        self.endpoint = "https://api.replicate.com/v1/predictions"
        
        if not REPLICATE_AVAILABLE:
            raise ImportError("Replicate package is required for Replicate image provider")
        
        # Initialize Replicate client
        replicate.Client(api_token=self.api_key)
        
        logger.info(f"🎨 Replicate Image Provider initialized: model={self.model}")
    
    async def generate_image(self, prompt: str, **kwargs) -> ImageResponse:
        """Generate image using Replicate"""
        try:
            # Override config with kwargs if provided
            model = kwargs.get("model", self.model)
            width = kwargs.get("width", self.width)
            height = kwargs.get("height", self.height)
            steps = kwargs.get("steps", self.steps)
            reference_image = kwargs.get("reference_image")
            
            logger.info(f"🎨 Generating image with Replicate: prompt='{prompt[:50]}...', model={model}")
            
            # Prepare input parameters
            input_kwargs = {
                "prompt": prompt,
                "width": width,
                "height": height,
                "steps": steps
            }
            
            # Add reference image if provided
            if reference_image:
                input_kwargs["image"] = reference_image
                logger.info("Reference image added to Replicate request")
            
            # Add any additional parameters from kwargs
            for key, value in kwargs.items():
                if key not in ["model", "width", "height", "steps", "reference_image"]:
                    input_kwargs[key] = value
            
            # Special handling for InstantID models
            if "instant-id" in model.lower():
                input_kwargs.update({
                    "ipadapter_weight": kwargs.get("ipadapter_weight", 0.7),
                    "instantid_weight": kwargs.get("instantid_weight", 0.6)
                })
            
            logger.info(f"Replicate input parameters: {input_kwargs}")
            
            # Call Replicate API
            output = replicate.run(model, input=input_kwargs)
            
            # Extract URLs from output
            urls = self._extract_urls_from_output(output)
            
            if not urls:
                raise ValueError("No image URLs received from Replicate")
            
            logger.info(f"✅ Replicate image generation successful: {len(urls)} images")
            
            return ImageResponse(
                urls=urls,
                model=model,
                prompt=prompt,
                metadata={
                    "provider": "replicate",
                    "width": width,
                    "height": height,
                    "steps": steps,
                    "reference_image": bool(reference_image)
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Replicate image generation failed: {e}")
            raise Exception(f"Replicate image generation error: {str(e)}")
    
    async def generate_image_with_http(self, prompt: str, **kwargs) -> ImageResponse:
        """Generate image using direct HTTP API (alternative method)"""
        try:
            headers = {
                "Authorization": f"Token {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "version": self.version or kwargs.get("version"),
                "input": {"prompt": prompt}
            }
            
            # Add reference image if provided
            reference_image = kwargs.get("reference_image")
            if reference_image:
                payload["input"]["image"] = reference_image
                logger.info("Reference image added to HTTP request")
            
            # Add other parameters
            for k, v in kwargs.items():
                if k != "reference_image":
                    payload["input"][k] = v
            
            logger.info(f"Replicate HTTP request payload: {payload}")
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.endpoint, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                
                # Extract URLs from response
                urls = data.get("output", [])
                if isinstance(urls, str):
                    urls = [urls]
                
                return ImageResponse(
                    urls=urls,
                    model=self.model,
                    prompt=prompt,
                    metadata={
                        "provider": "replicate",
                        "method": "http_api",
                        "prediction_id": data.get("id")
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ Replicate HTTP image generation failed: {e}")
            raise Exception(f"Replicate HTTP image generation error: {str(e)}")
    
    def _extract_urls_from_output(self, output) -> List[str]:
        """Extract URLs from various output formats"""
        urls = []
        
        try:
            # Case 1: Direct string URL
            if isinstance(output, str) and output.startswith('http'):
                urls.append(output)
                logger.info(f"Single URL found: {output}")
                
            # Case 2: List of string URLs
            elif isinstance(output, list):
                for item in output:
                    if isinstance(item, str) and item.startswith('http'):
                        urls.append(item)
                        logger.info(f"URL from list: {item}")
                    # List of dict objects with url field
                    elif isinstance(item, dict) and 'url' in item:
                        urls.append(item['url'])
                        logger.info(f"URL from dict: {item['url']}")
                        
            # Case 3: Dict object with url field
            elif isinstance(output, dict) and 'url' in output:
                urls.append(output['url'])
                logger.info(f"URL from dict object: {output['url']}")
                
            # Case 4: Iterator/Generator
            else:
                try:
                    for item in output:
                        if isinstance(item, str) and item.startswith('http'):
                            urls.append(item)
                            logger.info(f"URL from iterator: {item}")
                        elif hasattr(item, 'url'):
                            urls.append(item.url)
                            logger.info(f"URL from iterator object: {item.url}")
                except TypeError:
                    # Not iterable
                    logger.warning(f"Unknown output format: {type(output)}")
                    
        except Exception as e:
            logger.error(f"Error extracting URLs: {e}")
        
        # If no URLs found, try to convert output to string as last resort
        if not urls:
            logger.warning(f"No URLs found in output: {output}")
            if output:
                urls = [str(output)]
        
        return urls
    
    def get_provider_info(self) -> Dict[str, Any]:
        """Get provider information"""
        return {
            "name": "replicate_image",
            "display_name": "Replicate",
            "type": "image",
            "supported_models": [
                "stability-ai/stable-diffusion",
                "stability-ai/sdxl",
                "zsxkib/instant-id-ipadapter-plus-face",
                "tencentarc/photomaker"
            ],
            "capabilities": ["text-to-image", "image-to-image", "reference-based-generation"],
            "features": ["custom_models", "reference_images", "high_resolution"],
            "is_available": REPLICATE_AVAILABLE and bool(self.api_key)
        }