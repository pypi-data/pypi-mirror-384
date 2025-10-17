"""Google Gemini provider implementation."""

from typing import Optional, AsyncIterator, List, Dict, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..base_provider import BaseLLMProvider
from ..settings import (
    GenerationRequest, 
    GenerationResponse, 
    StreamChunk, 
    ProviderInfo,
    Message,
    MessageRole
)
from ..utils.config import GeminiConfig, ProviderConfig
from ..utils.exceptions import (
    InvalidConfigurationError,
    AuthenticationError,
    APIError,
    RateLimitError,
    ModelNotAvailableError,
    GenerationError
)
from ..utils.logger import logger


class GeminiProvider(BaseLLMProvider):
    """Google Gemini LLM provider implementation."""
    
    SUPPORTED_MODELS = [
        "models/gemini-2.5-flash",
        "models/gemini-2.5-pro", 
        "models/gemini-2.0-flash",
        "models/gemini-flash-latest",
        "models/gemini-pro-latest",
        # Legacy support (might not work)
        "gemini-pro",
        "gemini-pro-vision",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-1.0-pro"
    ]
    
    def __init__(self, config: Optional[GeminiConfig] = None) -> None:
        """Initialize Gemini provider.
        
        Args:
            config: Gemini configuration. If None, will try to load from environment.
        """
        if config is None:
            config = GeminiConfig.from_env()
        
        super().__init__(config)
        self.model: Optional[genai.GenerativeModel] = None
        self.config: GeminiConfig = config
    
    def get_provider_info(self) -> ProviderInfo:
        """Get Gemini provider information."""
        return ProviderInfo(
            name="gemini",
            display_name="Google Gemini",
            description="Google's Gemini models for multimodal AI",
            supported_models=self.SUPPORTED_MODELS,
            capabilities=["chat", "completion", "streaming", "vision"],
            is_available=self.config.api_key is not None
        )
    
    async def initialize(self) -> None:
        """Initialize Gemini client."""
        if not self.validate_config():
            raise InvalidConfigurationError("Invalid Gemini configuration", "gemini")
        
        try:
            genai.configure(api_key=self.config.api_key)
            
            # Create generation config
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            
            # Safety settings - allow most content for flexibility
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            self.model = genai.GenerativeModel(
                model_name=self.config.model,
                generation_config=generation_config,
                safety_settings=safety_settings
            )
            
            logger.info("Gemini client initialized successfully", "gemini")
            
        except Exception as e:
            if "API_KEY" in str(e).upper():
                raise AuthenticationError(f"Gemini authentication failed: {str(e)}", "gemini")
            else:
                raise APIError(f"Failed to initialize Gemini client: {str(e)}", "gemini")
    
    def validate_config(self) -> bool:
        """Validate Gemini configuration."""
        if not self.config.api_key:
            raise InvalidConfigurationError("Gemini API key is required", "gemini")
        
        if self.config.model not in self.SUPPORTED_MODELS:
            raise InvalidConfigurationError(
                f"Model '{self.config.model}' is not supported. "
                f"Supported models: {', '.join(self.SUPPORTED_MODELS)}", 
                "gemini"
            )
        
        return True
    
    def is_available(self) -> bool:
        """Check if Gemini provider is available."""
        return bool(self.config.api_key)
    
    def get_supported_models(self) -> List[str]:
        """Get supported Gemini models."""
        return self.SUPPORTED_MODELS.copy()
    
    def _convert_messages(self, request: GenerationRequest) -> List[Dict[str, str]]:
        """Convert request to Gemini message format."""
        messages = []
        
        # Process conversation history
        if request.history:
            for msg in request.history:
                # Gemini doesn't have a system role, so we'll convert system messages to user messages
                role = "user" if msg.role == MessageRole.SYSTEM else msg.role.value
                if role == "assistant":
                    role = "model"  # Gemini uses "model" instead of "assistant"
                
                messages.append({
                    "role": role,
                    "parts": [msg.content]
                })
        
        # Add current prompt as user message
        messages.append({
            "role": "user",
            "parts": [request.prompt]
        })
        
        return messages
    
    def _parse_finish_reason(self, finish_reason: Optional[str]) -> Optional[str]:
        """Parse Gemini finish reason."""
        if not finish_reason:
            return None
        
        reason_map = {
            "STOP": "stop",
            "MAX_TOKENS": "max_tokens",
            "SAFETY": "safety",
            "RECITATION": "recitation",
            "OTHER": "other"
        }
        
        return reason_map.get(finish_reason, finish_reason.lower())
    
    async def generate(self, request: GenerationRequest) -> GenerationResponse:
        """Generate text using Gemini API."""
        await self.ensure_initialized()
        
        try:
            # Create generation config for this request
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
            )
            
            if request.top_p is not None:
                generation_config.top_p = request.top_p
            
            if request.stop_sequences:
                generation_config.stop_sequences = request.stop_sequences
            
            # Safety settings for generation
            safety_settings = {
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
            
            # Prepare content
            if request.history:
                # Use chat format for conversation
                messages = self._convert_messages(request)
                chat = self.model.start_chat(history=messages[:-1])  # Exclude the last message (current prompt)
                
                logger.debug(f"Making Gemini chat API call with model: {self.config.model}", "gemini")
                response = await chat.send_message_async(
                    request.prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
            else:
                # Use simple generation for single prompt
                logger.debug(f"Making Gemini generate API call with model: {self.config.model}", "gemini")
                response = await self.model.generate_content_async(
                    request.prompt,
                    generation_config=generation_config,
                    safety_settings=safety_settings
                )
            
            # Extract content with safety check
            content = ""
            try:
                # Try response.text first (most common case)
                if hasattr(response, 'text') and response.text:
                    content = response.text
                else:
                    raise ValueError("No response.text available")
            except (ValueError, AttributeError, Exception) as e:
                # Fallback to manual extraction
                if response.candidates and len(response.candidates) > 0:
                    candidate = response.candidates[0]
                    if candidate.content and candidate.content.parts:
                        content = "".join([part.text for part in candidate.content.parts if hasattr(part, 'text')])
                    elif candidate.safety_ratings:
                        # Response was blocked by safety filters
                        safety_reasons = [rating.category.name for rating in candidate.safety_ratings 
                                        if rating.probability.name in ['HIGH', 'MEDIUM']]
                        if safety_reasons:
                            content = f"Response blocked by safety filters: {', '.join(safety_reasons)}"
                        else:
                            content = "Response blocked by safety filters"
                    else:
                        content = "No content generated"
                else:
                    content = f"Empty response from Gemini: {str(e)}"
            
            # Get usage information if available
            usage = None
            if hasattr(response, 'usage_metadata') and response.usage_metadata:
                usage = {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                }
            
            # Get finish reason
            finish_reason = None
            if response.candidates and response.candidates[0].finish_reason:
                finish_reason = self._parse_finish_reason(response.candidates[0].finish_reason.name)
            
            return GenerationResponse(
                content=content,
                finish_reason=finish_reason,
                usage=usage,
                provider="gemini",
                model=self.config.model,
                metadata={
                    "safety_ratings": [
                        {
                            "category": rating.category.name,
                            "probability": rating.probability.name
                        }
                        for rating in (response.candidates[0].safety_ratings if response.candidates else [])
                    ]
                }
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate" in error_msg:
                raise RateLimitError(f"Gemini rate limit exceeded: {str(e)}", "gemini")
            elif "api" in error_msg and "key" in error_msg:
                raise AuthenticationError(f"Gemini authentication error: {str(e)}", "gemini")
            elif "model" in error_msg and "not found" in error_msg:
                raise ModelNotAvailableError(f"Gemini model not found: {str(e)}", self.config.model, "gemini")
            else:
                raise GenerationError(f"Gemini generation failed: {str(e)}", "gemini")
    
    async def stream_generate(self, request: GenerationRequest) -> AsyncIterator[StreamChunk]:
        """Generate text with streaming using Gemini API."""
        await self.ensure_initialized()
        
        try:
            # Create generation config for this request
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
            )
            
            if request.top_p is not None:
                generation_config.top_p = request.top_p
            
            if request.stop_sequences:
                generation_config.stop_sequences = request.stop_sequences
            
            logger.debug(f"Starting Gemini streaming with model: {self.config.model}", "gemini")
            
            # Prepare content
            if request.history:
                # Use chat format for conversation
                messages = self._convert_messages(request)
                chat = self.model.start_chat(history=messages[:-1])  # Exclude the last message (current prompt)
                
                response_stream = await chat.send_message_async(
                    request.prompt,
                    generation_config=generation_config,
                    stream=True
                )
            else:
                # Use simple generation for single prompt
                response_stream = await self.model.generate_content_async(
                    request.prompt,
                    generation_config=generation_config,
                    stream=True
                )
            
            async for chunk in response_stream:
                if chunk.text:
                    yield StreamChunk(
                        content=chunk.text,
                        is_final=False,
                        metadata={
                            "safety_ratings": [
                                {
                                    "category": rating.category.name,
                                    "probability": rating.probability.name
                                }
                                for rating in (chunk.candidates[0].safety_ratings if chunk.candidates else [])
                            ]
                        }
                    )
            
            # Send final chunk
            yield StreamChunk(
                content="",
                is_final=True,
                finish_reason="stop"
            )
            
        except Exception as e:
            error_msg = str(e).lower()
            
            if "quota" in error_msg or "rate" in error_msg:
                raise RateLimitError(f"Gemini rate limit exceeded: {str(e)}", "gemini")
            elif "api" in error_msg and "key" in error_msg:
                raise AuthenticationError(f"Gemini authentication error: {str(e)}", "gemini")
            elif "model" in error_msg and "not found" in error_msg:
                raise ModelNotAvailableError(f"Gemini model not found: {str(e)}", self.config.model, "gemini")
            else:
                raise GenerationError(f"Gemini streaming failed: {str(e)}", "gemini")