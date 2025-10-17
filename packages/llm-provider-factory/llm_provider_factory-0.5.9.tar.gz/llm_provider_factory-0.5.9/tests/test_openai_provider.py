"""Tests for OpenAI provider."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from llm_provider import (
    OpenAIProvider,
    OpenAIConfig,
    GenerationRequest,
    Message,
    MessageRole,
    InvalidConfigurationError,
    AuthenticationError,
    APIError
)


class TestOpenAIProvider:
    """Test cases for OpenAI provider."""
    
    def test_provider_info(self):
        """Test OpenAI provider information."""
        config = OpenAIConfig(api_key="sk-test-api-key-not-real")
        provider = OpenAIProvider(config)
        
        info = provider.get_provider_info()
        assert info.name == "openai"
        assert info.display_name == "OpenAI"
        assert "gpt-4" in info.supported_models
        assert "gpt-3.5-turbo" in info.supported_models
        assert "chat" in info.capabilities
        assert info.is_available is True
    
    def test_provider_info_without_api_key(self):
        """Test provider info when API key is missing."""
        config = OpenAIConfig(api_key=None)
        provider = OpenAIProvider(config)
        
        info = provider.get_provider_info()
        assert info.is_available is False
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = OpenAIConfig(api_key="test-key", model="gpt-3.5-turbo")
        provider = OpenAIProvider(config)
        
        assert provider.validate_config() is True
    
    def test_config_validation_missing_api_key(self):
        """Test configuration validation with missing API key."""
        config = OpenAIConfig(api_key=None)
        provider = OpenAIProvider(config)
        
        with pytest.raises(InvalidConfigurationError):
            provider.validate_config()
    
    def test_config_validation_unsupported_model(self):
        """Test configuration validation with unsupported model."""
        config = OpenAIConfig(api_key="test-key", model="unsupported-model")
        provider = OpenAIProvider(config)
        
        with pytest.raises(InvalidConfigurationError):
            provider.validate_config()
    
    def test_supported_models(self):
        """Test getting supported models."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        models = provider.get_supported_models()
        assert "gpt-4" in models
        assert "gpt-3.5-turbo" in models
        assert "gpt-4o" in models
    
    def test_is_model_supported(self):
        """Test checking if a model is supported."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        assert provider.is_model_supported("gpt-4") is True
        assert provider.is_model_supported("gpt-3.5-turbo") is True
        assert provider.is_model_supported("unsupported-model") is False
    
    def test_convert_messages_simple(self):
        """Test converting simple messages."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        request = GenerationRequest(prompt="Hello")
        messages = provider._convert_messages(request)
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
    
    def test_convert_messages_with_history(self):
        """Test converting messages with history."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        history = [
            Message(role=MessageRole.USER, content="Hi"),
            Message(role=MessageRole.ASSISTANT, content="Hello!")
        ]
        request = GenerationRequest(prompt="How are you?", history=history)
        messages = provider._convert_messages(request)
        
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hi"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hello!"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "How are you?"
    
    def test_parse_finish_reason(self):
        """Test parsing finish reasons."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        assert provider._parse_finish_reason("stop") == "stop"
        assert provider._parse_finish_reason("length") == "max_tokens"
        assert provider._parse_finish_reason("content_filter") == "content_filter"
        assert provider._parse_finish_reason(None) is None
        assert provider._parse_finish_reason("unknown") == "unknown"
    
    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful provider initialization."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = Mock()
            mock_client.models.list = AsyncMock(return_value=[])
            mock_client_class.return_value = mock_client
            
            await provider.initialize()
            
            assert provider.client == mock_client
            mock_client_class.assert_called_once_with(
                api_key="test-key",
                organization=None,
                base_url=None,
                timeout=30
            )
    
    @pytest.mark.asyncio
    async def test_initialization_auth_error(self):
        """Test initialization with authentication error."""
        config = OpenAIConfig(api_key="invalid-key")
        provider = OpenAIProvider(config)
        
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = Mock()
            mock_client.models.list = AsyncMock(side_effect=Exception("Authentication failed"))
            mock_client_class.return_value = mock_client
            
            with pytest.raises(APIError):
                await provider.initialize()
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful text generation."""
        config = OpenAIConfig(api_key="test-key")
        provider = OpenAIProvider(config)
        
        # Mock the OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_response.id = "test-id"
        mock_response.created = 1234567890
        mock_response.system_fingerprint = "test-fingerprint"
        
        with patch('openai.AsyncOpenAI') as mock_client_class:
            mock_client = Mock()
            mock_client.models.list = AsyncMock(return_value=[])
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            await provider.initialize()
            
            request = GenerationRequest(prompt="Test prompt")
            response = await provider.generate(request)
            
            assert response.content == "Generated text"
            assert response.finish_reason == "stop"
            assert response.provider == "openai"
            assert response.usage["total_tokens"] == 15
    
    def test_string_representations(self):
        """Test string representations of provider."""
        config = OpenAIConfig(api_key="test-key", model="gpt-4")
        provider = OpenAIProvider(config)
        
        str_repr = str(provider)
        assert "OpenAIProvider" in str_repr
        assert "gpt-4" in str_repr
        
        repr_str = repr(provider)
        assert "OpenAIProvider" in repr_str
        assert "initialized=False" in repr_str