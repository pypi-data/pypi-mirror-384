"""Configuration management for LLM Provider Factory."""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import os


class ProviderConfig(BaseModel):
    """Base configuration for LLM providers."""
    
    api_key: Optional[str] = None
    model: str = Field(..., description="Model name to use")
    max_tokens: int = Field(default=1000, ge=1, le=100000)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    timeout: int = Field(default=30, ge=1, le=300)
    
    class Config:
        extra = "allow"  # Allow additional fields for provider-specific configs


class OpenAIConfig(ProviderConfig):
    """Configuration for OpenAI provider."""
    
    model: str = Field(default="gpt-3.5-turbo")
    organization: Optional[str] = None
    base_url: Optional[str] = None
    
    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY"),
            organization=os.getenv("OPENAI_ORGANIZATION"),
            model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("OPENAI_TIMEOUT", "30")),
        )


class AnthropicConfig(ProviderConfig):
    """Configuration for Anthropic provider."""
    
    model: str = Field(default="claude-3-sonnet-20240229")
    
    @classmethod
    def from_env(cls) -> "AnthropicConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            model=os.getenv("ANTHROPIC_MODEL", "claude-3-sonnet-20240229"),
            max_tokens=int(os.getenv("ANTHROPIC_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("ANTHROPIC_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("ANTHROPIC_TIMEOUT", "30")),
        )


class GeminiConfig(ProviderConfig):
    """Configuration for Google Gemini provider."""
    
    model: str = Field(default="gemini-pro")
    
    @classmethod
    def from_env(cls) -> "GeminiConfig":
        """Create config from environment variables."""
        return cls(
            api_key=os.getenv("GOOGLE_API_KEY"),
            model=os.getenv("GEMINI_MODEL", "gemini-pro"),
            max_tokens=int(os.getenv("GEMINI_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("GEMINI_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("GEMINI_TIMEOUT", "30")),
        )


class VertexAIConfig(ProviderConfig):
    """Configuration for Google Cloud Vertex AI provider."""
    
    model: str = Field(default="gemini-1.5-flash")
    project_id: str = Field(..., description="Google Cloud Project ID")
    location: str = Field(default="us-central1", description="Google Cloud region")
    credentials_path: Optional[str] = Field(default=None, description="Path to service account JSON file")
    
    @classmethod
    def from_env(cls) -> "VertexAIConfig":
        """Create config from environment variables."""
        return cls(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            location=os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1"),
            model=os.getenv("VERTEXAI_MODEL", "gemini-1.5-flash"),
            credentials_path=os.getenv("GOOGLE_APPLICATION_CREDENTIALS"),
            max_tokens=int(os.getenv("VERTEXAI_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("VERTEXAI_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("VERTEXAI_TIMEOUT", "30")),
        )


class ConfigManager:
    """Manages configurations for all providers."""
    
    def __init__(self) -> None:
        self._configs: Dict[str, ProviderConfig] = {}
    
    def set_config(self, provider_name: str, config: ProviderConfig) -> None:
        """Set configuration for a provider."""
        self._configs[provider_name.lower()] = config
    
    def get_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a provider."""
        return self._configs.get(provider_name.lower())
    
    def load_from_env(self) -> None:
        """Load configurations from environment variables."""
        if os.getenv("OPENAI_API_KEY"):
            self.set_config("openai", OpenAIConfig.from_env())
        
        if os.getenv("ANTHROPIC_API_KEY"):
            self.set_config("anthropic", AnthropicConfig.from_env())
        
        if os.getenv("GOOGLE_API_KEY"):
            self.set_config("gemini", GeminiConfig.from_env())
        
        if os.getenv("GOOGLE_CLOUD_PROJECT"):
            self.set_config("vertexai", VertexAIConfig.from_env())
        
        if os.getenv("OLLAMA_BASE_URL"):
            self.set_config("ollama", OllamaConfig.from_env())


class OllamaConfig(ProviderConfig):
    """Configuration for Ollama provider."""
    
    model: str = Field(default="llama2")
    base_url: str = Field(default="http://localhost:11434")
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Create config from environment variables."""
        return cls(
            api_key=None,  # Ollama doesn't need API key
            model=os.getenv("OLLAMA_MODEL", "llama2"),
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            max_tokens=int(os.getenv("OLLAMA_MAX_TOKENS", "1000")),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
            timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")),
        )


class OpenAIImageConfig(ProviderConfig):
    """OpenAI DALL-E image configuration"""
    api_key: str
    model: str = "dall-e-3"
    size: str = "1024x1024"
    quality: str = "standard"
    style: str = "vivid"
    n: int = 1
    timeout: int = 60


class ReplicateImageConfig(ProviderConfig):
    """Replicate image configuration"""
    api_key: str
    model: str = "stability-ai/stable-diffusion"
    version: Optional[str] = None
    width: int = 1024
    height: int = 1024
    steps: int = 50
    timeout: int = 120


# Global config manager
config_manager = ConfigManager()