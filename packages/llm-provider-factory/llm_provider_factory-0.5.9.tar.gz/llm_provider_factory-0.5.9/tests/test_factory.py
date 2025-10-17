"""Tests for LLMProviderFactory."""

import pytest
from unittest.mock import Mock, AsyncMock
from llm_provider import (
    LLMProviderFactory, 
    OpenAI, 
    Anthropic, 
    Gemini,
    OpenAIConfig,
    GenerationRequest,
    GenerationResponse,
    Message,
    MessageRole,
    ProviderNotFoundError,
    InvalidConfigurationError
)


class MockProvider:
    """Mock provider for testing."""
    
    def __init__(self, name="mock"):
        self.provider_name = name
        self._is_initialized = False
    
    async def initialize(self):
        self._is_initialized = True
    
    async def ensure_initialized(self):
        if not self._is_initialized:
            await self.initialize()
    
    async def generate(self, request):
        return GenerationResponse(
            content="Mock response",
            provider=self.provider_name
        )
    
    async def stream_generate(self, request):
        yield {"content": "Mock", "is_final": False}
        yield {"content": " stream", "is_final": True}
    
    def get_provider_info(self):
        return {
            "name": self.provider_name,
            "display_name": "Mock Provider",
            "description": "Mock provider for testing",
            "supported_models": ["mock-model"],
            "capabilities": ["chat"],
            "is_available": True
        }


class TestLLMProviderFactory:
    """Test cases for LLMProviderFactory."""
    
    def test_factory_initialization_without_provider(self):
        """Test factory initialization without a provider."""
        factory = LLMProviderFactory()
        assert factory.get_current_provider() is None
        assert "openai" in factory.get_available_providers()
        assert "anthropic" in factory.get_available_providers()
        assert "gemini" in factory.get_available_providers()
    
    def test_factory_initialization_with_provider(self):
        """Test factory initialization with a provider."""
        mock_provider = MockProvider()
        factory = LLMProviderFactory(mock_provider)
        assert factory.get_current_provider() == mock_provider
    
    def test_register_provider(self):
        """Test registering a new provider."""
        factory = LLMProviderFactory()
        
        class CustomProvider:
            pass
        
        factory.register_provider("custom", CustomProvider)
        assert "custom" in factory.get_available_providers()
    
    def test_create_provider_success(self):
        """Test creating a provider successfully."""
        factory = LLMProviderFactory()
        
        # Mock the provider creation to avoid needing real API keys
        original_providers = factory._providers.copy()
        factory._providers["mock"] = MockProvider
        
        provider = factory.create_provider("mock")
        assert isinstance(provider, MockProvider)
        
        # Restore original providers
        factory._providers = original_providers
    
    def test_create_provider_not_found(self):
        """Test creating a non-existent provider."""
        factory = LLMProviderFactory()
        
        with pytest.raises(ProviderNotFoundError):
            factory.create_provider("nonexistent")
    
    def test_set_provider_by_instance(self):
        """Test setting provider by instance."""
        factory = LLMProviderFactory()
        mock_provider = MockProvider()
        
        factory.set_provider(mock_provider)
        assert factory.get_current_provider() == mock_provider
    
    @pytest.mark.asyncio
    async def test_generate_with_current_provider(self):
        """Test generation with current provider."""
        mock_provider = MockProvider()
        factory = LLMProviderFactory(mock_provider)
        
        response = await factory.generate("Test prompt")
        assert response.content == "Mock response"
        assert response.provider == "mock"
    
    @pytest.mark.asyncio
    async def test_generate_without_provider(self):
        """Test generation without setting a provider."""
        factory = LLMProviderFactory()
        
        with pytest.raises(InvalidConfigurationError):
            await factory.generate("Test prompt")
    
    @pytest.mark.asyncio
    async def test_generate_with_history(self):
        """Test generation with conversation history."""
        mock_provider = MockProvider()
        factory = LLMProviderFactory(mock_provider)
        
        history = [
            Message(role=MessageRole.USER, content="Hello"),
            Message(role=MessageRole.ASSISTANT, content="Hi there!")
        ]
        
        response = await factory.generate("How are you?", history=history)
        assert response.content == "Mock response"
    
    @pytest.mark.asyncio
    async def test_stream_generate(self):
        """Test streaming generation."""
        mock_provider = MockProvider()
        factory = LLMProviderFactory(mock_provider)
        
        chunks = []
        async for chunk in factory.stream_generate("Test prompt"):
            chunks.append(chunk)
        
        assert len(chunks) == 2
        assert chunks[0]["content"] == "Mock"
        assert chunks[1]["is_final"] is True
    
    def test_convenience_methods(self):
        """Test convenience factory creation methods."""
        # Note: These would normally require valid API keys
        # In a real test environment, you'd mock the provider initialization
        
        # Test that the methods exist and return factory instances
        assert hasattr(LLMProviderFactory, 'create_openai')
        assert hasattr(LLMProviderFactory, 'create_anthropic')
        assert hasattr(LLMProviderFactory, 'create_gemini')
    
    def test_string_representations(self):
        """Test string representations of factory."""
        factory = LLMProviderFactory()
        str_repr = str(factory)
        assert "LLMProviderFactory" in str_repr
        assert "current_provider=None" in str_repr
        
        repr_str = repr(factory)
        assert "LLMProviderFactory" in repr_str


class TestFactoryProviderIntegration:
    """Integration tests for factory with different providers."""
    
    def test_provider_info_retrieval(self):
        """Test retrieving provider information."""
        factory = LLMProviderFactory()
        
        # Mock providers to avoid API key requirements
        mock_provider = MockProvider("openai")
        factory._provider_instances["openai"] = mock_provider
        
        info = factory.get_provider_info("openai")
        assert info["name"] == "openai"
        assert info["display_name"] == "Mock Provider"
    
    def test_get_all_provider_info(self):
        """Test retrieving all provider information."""
        factory = LLMProviderFactory()
        
        # Mock all providers
        for name in ["openai", "anthropic", "gemini"]:
            mock_provider = MockProvider(name)
            factory._provider_instances[name] = mock_provider
        
        all_info = factory.get_provider_info()
        assert len(all_info) >= 3  # At least the three main providers