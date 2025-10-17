"""Tests for VertexAI provider."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from llm_provider import (
    VertexAIProvider,
    VertexAIConfig,
    GenerationRequest,
    Message,
    MessageRole,
    InvalidConfigurationError,
    AuthenticationError,
    APIError
)


class TestVertexAIProvider:
    """Test cases for VertexAI provider."""
    
    def test_provider_info(self):
        """Test VertexAI provider information."""
        config = VertexAIConfig(
            project_id="test-project",
            credentials_path="test-credentials.json"
        )
        provider = VertexAIProvider(config)
        
        info = provider.get_provider_info()
        assert info.name == "vertexai"
        assert info.display_name == "Google Cloud Vertex AI"
        assert "gemini-1.5-pro" in info.supported_models
        assert "gemini-1.5-flash" in info.supported_models
        assert "chat" in info.capabilities
    
    def test_provider_info_without_credentials(self):
        """Test provider info when credentials are missing."""
        config = VertexAIConfig(project_id=None)
        provider = VertexAIProvider(config)
        
        info = provider.get_provider_info()
        assert info.is_available is False
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        config = VertexAIConfig(
            project_id="test-project",
            credentials_path="test-credentials.json",
            model="gemini-1.5-flash"
        )
        provider = VertexAIProvider(config)
        
        with patch.dict('os.environ', {'GOOGLE_APPLICATION_CREDENTIALS': 'test.json'}):
            assert provider.validate_config() is True
    
    def test_config_validation_missing_project(self):
        """Test configuration validation with missing project ID."""
        config = VertexAIConfig(project_id=None)
        provider = VertexAIProvider(config)
        
        with pytest.raises(InvalidConfigurationError):
            provider.validate_config()
    
    def test_config_validation_unsupported_model(self):
        """Test configuration validation with unsupported model."""
        config = VertexAIConfig(
            project_id="test-project",
            credentials_path="test-credentials.json",
            model="unsupported-model"
        )
        provider = VertexAIProvider(config)
        
        with pytest.raises(InvalidConfigurationError):
            provider.validate_config()
    
    def test_config_validation_missing_credentials(self):
        """Test configuration validation with missing credentials."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        with patch.dict('os.environ', {}, clear=True):
            with pytest.raises(InvalidConfigurationError):
                provider.validate_config()
    
    def test_supported_models(self):
        """Test getting supported models."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        models = provider.get_supported_models()
        assert "gemini-1.5-pro" in models
        assert "gemini-1.5-flash" in models
        assert "text-bison" in models
    
    def test_is_model_supported(self):
        """Test checking if a model is supported."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        assert provider.is_model_supported("gemini-1.5-flash") is True
        assert provider.is_model_supported("gemini-1.5-pro") is True
        assert provider.is_model_supported("unsupported-model") is False
    
    def test_convert_messages_simple(self):
        """Test converting simple messages."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        request = GenerationRequest(prompt="Hello")
        prompt = provider._convert_messages(request)
        
        assert "User: Hello" in prompt
        assert "Assistant:" in prompt
    
    def test_convert_messages_with_history(self):
        """Test converting messages with history."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        history = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant"),
            Message(role=MessageRole.USER, content="Hi"),
            Message(role=MessageRole.ASSISTANT, content="Hello!")
        ]
        request = GenerationRequest(prompt="How are you?", history=history)
        prompt = provider._convert_messages(request)
        
        assert "System: You are a helpful assistant" in prompt
        assert "User: Hi" in prompt
        assert "Assistant: Hello!" in prompt
        assert "User: How are you?" in prompt
    
    def test_parse_finish_reason(self):
        """Test parsing finish reasons."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        assert provider._parse_finish_reason("STOP") == "stop"
        assert provider._parse_finish_reason("MAX_TOKENS") == "max_tokens"
        assert provider._parse_finish_reason("SAFETY") == "safety"
        assert provider._parse_finish_reason(None) is None
        assert provider._parse_finish_reason("UNKNOWN") == "unknown"
    
    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """Test successful provider initialization."""
        config = VertexAIConfig(
            project_id="test-project",
            credentials_path="test-credentials.json"
        )
        provider = VertexAIProvider(config)
        
        with patch('llm_provider.providers.vertexai_provider.VERTEXAI_AVAILABLE', True):
            with patch('llm_provider.providers.vertexai_provider.aiplatform') as mock_aiplatform:
                with patch('llm_provider.providers.vertexai_provider.GenerativeModel') as mock_model_class:
                    mock_model = Mock()
                    mock_model_class.return_value = mock_model
                    
                    await provider.initialize()
                    
                    mock_aiplatform.init.assert_called_once_with(
                        project="test-project",
                        location="us-central1"
                    )
                    assert provider.model == mock_model
    
    @pytest.mark.asyncio
    async def test_initialization_missing_package(self):
        """Test initialization with missing package."""
        config = VertexAIConfig(project_id="test-project")
        provider = VertexAIProvider(config)
        
        with patch('llm_provider.providers.vertexai_provider.VERTEXAI_AVAILABLE', False):
            with pytest.raises(InvalidConfigurationError):
                await provider.initialize()
    
    @pytest.mark.asyncio
    async def test_generate_success(self):
        """Test successful text generation."""
        config = VertexAIConfig(
            project_id="test-project",
            credentials_path="test-credentials.json"
        )
        provider = VertexAIProvider(config)
        
        # Mock the Vertex AI response
        mock_response = Mock()
        mock_response.text = "Generated text from Vertex AI"
        mock_response.candidates = [Mock()]
        mock_response.candidates[0].finish_reason = Mock()
        mock_response.candidates[0].finish_reason.name = "STOP"
        mock_response.candidates[0].safety_ratings = []
        mock_response.usage_metadata = Mock()
        mock_response.usage_metadata.prompt_token_count = 10
        mock_response.usage_metadata.candidates_token_count = 5
        mock_response.usage_metadata.total_token_count = 15
        
        with patch('llm_provider.providers.vertexai_provider.VERTEXAI_AVAILABLE', True):
            with patch('llm_provider.providers.vertexai_provider.aiplatform'):
                with patch('llm_provider.providers.vertexai_provider.GenerativeModel') as mock_model_class:
                    mock_model = Mock()
                    mock_model.generate_content.return_value = mock_response
                    mock_model_class.return_value = mock_model
                    
                    await provider.initialize()
                    
                    request = GenerationRequest(prompt="Test prompt")
                    response = await provider.generate(request)
                    
                    assert response.content == "Generated text from Vertex AI"
                    assert response.finish_reason == "stop"
                    assert response.provider == "vertexai"
                    assert response.usage["total_tokens"] == 15
    
    def test_string_representations(self):
        """Test string representations of provider."""
        config = VertexAIConfig(
            project_id="test-project",
            model="gemini-1.5-flash"
        )
        provider = VertexAIProvider(config)
        
        str_repr = str(provider)
        assert "VertexAIProvider" in str_repr
        assert "gemini-1.5-flash" in str_repr
        
        repr_str = repr(provider)
        assert "VertexAIProvider" in repr_str
        assert "initialized=False" in repr_str
    
    def test_config_from_env(self):
        """Test creating config from environment variables."""
        env_vars = {
            'GOOGLE_CLOUD_PROJECT': 'test-project',
            'GOOGLE_CLOUD_LOCATION': 'europe-west1',
            'GOOGLE_APPLICATION_CREDENTIALS': 'service-account.json',
            'VERTEXAI_MODEL': 'gemini-1.5-pro',
            'VERTEXAI_MAX_TOKENS': '2000',
            'VERTEXAI_TEMPERATURE': '0.8',
            'VERTEXAI_TIMEOUT': '60'
        }
        
        with patch.dict('os.environ', env_vars):
            config = VertexAIConfig.from_env()
            
            assert config.project_id == "test-project"
            assert config.location == "europe-west1"
            assert config.credentials_path == "service-account.json"
            assert config.model == "gemini-1.5-pro"
            assert config.max_tokens == 2000
            assert config.temperature == 0.8
            assert config.timeout == 60