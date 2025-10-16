"""Custom exceptions for LLM Provider Factory."""

from typing import Optional, Any


class LLMProviderError(Exception):
    """Base exception for all LLM provider errors."""
    
    def __init__(self, message: str, provider: Optional[str] = None, **kwargs: Any) -> None:
        self.provider = provider
        self.details = kwargs
        super().__init__(message)


class ProviderNotFoundError(LLMProviderError):
    """Raised when a requested provider is not available."""
    pass


class InvalidConfigurationError(LLMProviderError):
    """Raised when provider configuration is invalid."""
    pass


class APIError(LLMProviderError):
    """Raised when API call fails."""
    
    def __init__(self, message: str, provider: Optional[str] = None, 
                 status_code: Optional[int] = None, **kwargs: Any) -> None:
        self.status_code = status_code
        super().__init__(message, provider, **kwargs)


class RateLimitError(APIError):
    """Raised when API rate limit is exceeded."""
    pass


class AuthenticationError(APIError):
    """Raised when API authentication fails."""
    pass


class ModelNotAvailableError(LLMProviderError):
    """Raised when requested model is not available."""
    
    def __init__(self, message: str, model: str, provider: Optional[str] = None, **kwargs: Any) -> None:
        self.model = model
        super().__init__(message, provider, **kwargs)


class GenerationError(LLMProviderError):
    """Raised when text generation fails."""
    pass