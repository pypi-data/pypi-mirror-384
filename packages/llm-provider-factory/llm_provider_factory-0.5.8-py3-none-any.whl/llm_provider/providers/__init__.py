"""LLM provider implementations."""

from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .gemini_provider import GeminiProvider
from .vertexai_provider import VertexAIProvider
from .ollama_provider import OllamaProvider

# Image providers
try:
    from .openai_image_provider import OpenAIImageProvider
except ImportError:
    OpenAIImageProvider = None

try:
    from .replicate_image_provider import ReplicateImageProvider
except ImportError:
    ReplicateImageProvider = None

# Create aliases for easier import
OpenAI = OpenAIProvider
Anthropic = AnthropicProvider
Gemini = GeminiProvider
VertexAI = VertexAIProvider
Ollama = OllamaProvider

__all__ = [
    "OpenAIProvider",
    "AnthropicProvider", 
    "GeminiProvider",
    "VertexAIProvider",
    "OllamaProvider",
    "OpenAI",
    "Anthropic",
    "Gemini",
    "VertexAI",
    "Ollama",
    # Image providers
    "OpenAIImageProvider",
    "ReplicateImageProvider",
]