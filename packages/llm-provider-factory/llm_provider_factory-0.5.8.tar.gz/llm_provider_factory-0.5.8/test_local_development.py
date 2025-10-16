"""
Lokal LLM Provider Factory Test Dosyası
Bu dosya ile kendi projenizdeki değişiklikleri test edebilirsiniz.
"""

import asyncio
import os
from llm_provider import (
    LLMProviderFactory,
    OpenAI, Anthropic, Gemini,
    OpenAIConfig, AnthropicConfig, GeminiConfig,
    Message, MessageRole
)

def test_basic_functionality():
    """Temel fonksiyonalite testleri."""
    print("🧪 Temel Fonksiyonalite Testleri")
    print("=" * 40)
    
    # Factory oluşturma
    factory = LLMProviderFactory()
    print(f"✅ Factory oluşturuldu: {factory}")
    
    # Mevcut provider'ları listele
    providers = factory.get_available_providers()
    print(f"✅ Mevcut provider'lar: {providers}")
    
    # Provider bilgileri
    for provider_name in providers:
        try:
            info = factory.get_provider_info(provider_name)
            print(f"📦 {info.display_name}: {len(info.supported_models)} model")
        except Exception as e:
            print(f"⚠️ {provider_name} bilgisi alınamadı: {e}")

def test_configuration():
    """Konfigürasyon testleri."""
    print("\n⚙️ Konfigürasyon Testleri")
    print("=" * 40)
    
    # Test konfigürasyonları oluştur
    configs = {
        "OpenAI": OpenAIConfig(
            api_key="test-key",
            model="gpt-3.5-turbo",
            temperature=0.8,
            max_tokens=150
        ),
        "Anthropic": AnthropicConfig(
            api_key="test-key",
            model="claude-3-sonnet-20240229",
            temperature=0.7,
            max_tokens=200
        ),
        "Gemini": GeminiConfig(
            api_key="test-key",
            model="gemini-pro",
            temperature=0.6,
            max_tokens=100
        )
    }
    
    for name, config in configs.items():
        print(f"✅ {name} Config - Model: {config.model}, Temp: {config.temperature}")

def test_provider_creation():
    """Provider oluşturma testleri."""
    print("\n🏭 Provider Oluşturma Testleri")
    print("=" * 40)
    
    try:
        # Farklı yöntemlerle provider oluşturma
        
        # Method 1: Direct instantiation
        openai_provider = OpenAI()
        factory1 = LLMProviderFactory(openai_provider)
        print(f"✅ Method 1 - Direct: {factory1.get_current_provider().provider_name}")
        
        # Method 2: Convenience methods
        factory2 = LLMProviderFactory.create_openai()
        print(f"✅ Method 2 - Convenience: {factory2.get_current_provider().provider_name}")
        
        # Method 3: Set provider by name
        factory3 = LLMProviderFactory()
        factory3.set_provider("anthropic")
        print(f"✅ Method 3 - By name: {factory3.get_current_provider().provider_name}")
        
    except Exception as e:
        print(f"⚠️ Provider oluşturma hatası (beklenen - API key yok): {type(e).__name__}")

def test_message_system():
    """Message sistemi testleri."""
    print("\n💬 Message Sistemi Testleri")
    print("=" * 40)
    
    # Conversation history oluştur
    history = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful AI assistant specialized in Python programming."),
        Message(role=MessageRole.USER, content="What is a lambda function?"),
        Message(role=MessageRole.ASSISTANT, content="A lambda function is a small anonymous function in Python that can have any number of arguments but can only have one expression."),
        Message(role=MessageRole.USER, content="Can you give me an example?")
    ]
    
    print(f"✅ Conversation history oluşturuldu: {len(history)} mesaj")
    for i, msg in enumerate(history):
        content_preview = msg.content[:50] + "..." if len(msg.content) > 50 else msg.content
        role_value = msg.role.value if hasattr(msg.role, 'value') else str(msg.role)
        print(f"  {i+1}. {role_value}: {content_preview}")

async def test_mock_generation():
    """Mock generation testleri (gerçek API çağrısı yapılmaz)."""
    print("\n🤖 Mock Generation Testleri")
    print("=" * 40)
    
    try:
        from llm_provider.settings import GenerationRequest, GenerationResponse, StreamChunk
        
        # Generation request oluştur
        request = GenerationRequest(
            prompt="Explain the concept of recursion in programming",
            max_tokens=200,
            temperature=0.7,
            top_p=0.9,
            stop_sequences=["END", "\n\n"]
        )
        
        print(f"✅ GenerationRequest oluşturuldu:")
        print(f"   Prompt: {request.prompt[:50]}...")
        print(f"   Max tokens: {request.max_tokens}")
        print(f"   Temperature: {request.temperature}")
        print(f"   Stop sequences: {request.stop_sequences}")
        
        # Mock response oluştur
        response = GenerationResponse(
            content="Recursion is a programming technique where a function calls itself...",
            finish_reason="stop",
            usage={"prompt_tokens": 15, "completion_tokens": 85, "total_tokens": 100},
            provider="mock",
            model="mock-model"
        )
        
        print(f"✅ GenerationResponse oluşturuldu:")
        print(f"   Content: {response.content[:50]}...")
        print(f"   Finish reason: {response.finish_reason}")
        print(f"   Usage: {response.usage}")
        
        # Mock stream chunk
        chunk = StreamChunk(
            content="This is a streaming chunk",
            is_final=False,
            metadata={"chunk_index": 1}
        )
        
        print(f"✅ StreamChunk oluşturuldu:")
        print(f"   Content: {chunk.content}")
        print(f"   Is final: {chunk.is_final}")
        
    except Exception as e:
        print(f"❌ Mock generation hatası: {e}")

def test_environment_variables():
    """Environment variable testleri."""
    print("\n🌍 Environment Variable Testleri")
    print("=" * 40)
    
    env_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY", 
        "GOOGLE_API_KEY"
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"✅ {var}: {masked_value}")
        else:
            print(f"⚠️ {var}: Not set")

async def test_with_real_api():
    """Gerçek API testi (sadece API key varsa)."""
    print("\n🌐 Gerçek API Testi")
    print("=" * 40)
    
    # OpenAI test
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            config = OpenAIConfig(api_key=openai_key, model="gpt-3.5-turbo")
            factory = LLMProviderFactory.create_openai(config)
            
            print("🔄 OpenAI API test ediliyor...")
            response = await factory.generate(
                "Hello! Please respond with just 'Hi there!' and nothing else.",
                max_tokens=10
            )
            print(f"✅ OpenAI Response: {response.content}")
            
        except Exception as e:
            print(f"❌ OpenAI API Error: {e}")
    else:
        print("⚠️ OPENAI_API_KEY not set, skipping real API test")
    
    # Anthropic test
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            config = AnthropicConfig(api_key=anthropic_key)
            factory = LLMProviderFactory.create_anthropic(config)
            
            print("🔄 Anthropic API test ediliyor...")
            response = await factory.generate(
                "Hello! Please respond with just 'Hi there!' and nothing else.",
                max_tokens=10
            )
            print(f"✅ Anthropic Response: {response.content}")
            
        except Exception as e:
            print(f"❌ Anthropic API Error: {e}")
    else:
        print("⚠️ ANTHROPIC_API_KEY not set, skipping real API test")

def test_error_handling():
    """Error handling testleri."""
    print("\n🚨 Error Handling Testleri")
    print("=" * 40)
    
    from llm_provider import (
        LLMProviderError,
        ProviderNotFoundError,
        InvalidConfigurationError,
        AuthenticationError
    )
    
    # Test 1: Non-existent provider
    try:
        factory = LLMProviderFactory()
        factory.create_provider("nonexistent")
    except ProviderNotFoundError as e:
        print(f"✅ ProviderNotFoundError caught: {e}")
    
    # Test 2: Invalid configuration
    try:
        config = OpenAIConfig(api_key=None)  # No API key
        provider = OpenAI(config)
        provider.validate_config()
    except InvalidConfigurationError as e:
        print(f"✅ InvalidConfigurationError caught: {e}")
    
    # Test 3: Generation without provider
    try:
        factory = LLMProviderFactory()
        # This should fail synchronously
        factory.generate("test")
    except Exception as e:
        print(f"✅ Error caught for missing provider: {type(e).__name__}")

async def main():
    """Ana test fonksiyonu."""
    print("🚀 LLM Provider Factory - Lokal Development Test")
    print("=" * 60)
    print("Bu test sizin lokal değişikliklerinizi test eder.")
    print("Kod değişikliği yaptıktan sonra bu dosyayı çalıştırın.")
    print("=" * 60)
    
    # Temel testler (API key gerektirmez)
    test_basic_functionality()
    test_configuration()
    test_provider_creation()
    test_message_system()
    
    # Async testler
    await test_mock_generation()
    
    # Environment ve error testleri
    test_environment_variables()
    test_error_handling()
    
    # Gerçek API testleri (isteğe bağlı)
    print("\n" + "=" * 40)
    choice = input("Gerçek API testi yapmak istiyor musunuz? (y/n): ").lower().strip()
    if choice in ['y', 'yes', 'evet']:
        await test_with_real_api()
    else:
        print("⏭️ Gerçek API testleri atlandı")
    
    print("\n🎉 Tüm testler tamamlandı!")
    print("💡 Tip: Kod değişikliği yaptıktan sonra bu scripti tekrar çalıştırın")

if __name__ == "__main__":
    asyncio.run(main())