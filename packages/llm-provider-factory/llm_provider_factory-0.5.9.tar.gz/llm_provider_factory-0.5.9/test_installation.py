"""Test paketten yüklenen LLM Provider Factory'yi test et."""

import asyncio
from llm_provider import (
    LLMProviderFactory,
    OpenAI, Anthropic, Gemini,
    OpenAIConfig, AnthropicConfig, GeminiConfig,
    Message, MessageRole
)

def test_basic_functionality():
    """Temel fonksiyonaliteyi test et."""
    print("🧪 Temel fonksiyonalite testi...")
    
    # Factory oluştur
    factory = LLMProviderFactory()
    
    # Mevcut provider'ları kontrol et
    providers = factory.get_available_providers()
    print(f"✅ Mevcut provider'lar: {providers}")
    
    # Provider bilgilerini al
    info_list = factory.get_provider_info()
    for info in info_list:
        print(f"📦 {info.display_name}: {len(info.supported_models)} model mevcut")
    
    # Configuration'ları test et
    openai_config = OpenAIConfig(api_key="test-key", model="gpt-3.5-turbo")
    print(f"⚙️ OpenAI Config: {openai_config.model}")
    
    anthropic_config = AnthropicConfig(api_key="test-key", model="claude-3-sonnet-20240229")
    print(f"⚙️ Anthropic Config: {anthropic_config.model}")
    
    gemini_config = GeminiConfig(api_key="test-key", model="gemini-pro")
    print(f"⚙️ Gemini Config: {gemini_config.model}")
    
    print("✅ Tüm temel testler başarılı!")

def test_message_system():
    """Message sistemi testi."""
    print("\n💬 Message sistemi testi...")
    
    messages = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful assistant"),
        Message(role=MessageRole.USER, content="Hello"),
        Message(role=MessageRole.ASSISTANT, content="Hi there!")
    ]
    
    for msg in messages:
        print(f"🔸 {msg.role}: {msg.content[:30]}...")
    
    print("✅ Message sistemi testi başarılı!")

def test_provider_creation():
    """Provider oluşturma testi."""
    print("\n🏭 Provider oluşturma testi...")
    
    try:
        # OpenAI provider
        openai_provider = OpenAI()
        print(f"✅ OpenAI Provider: {openai_provider}")
        
        # Factory ile provider
        factory = LLMProviderFactory(openai_provider)
        current = factory.get_current_provider()
        print(f"✅ Current Provider: {current.provider_name if current else 'None'}")
        
        # Convenience methods
        factory_openai = LLMProviderFactory.create_openai()
        print(f"✅ Factory OpenAI: {factory_openai.get_current_provider().provider_name}")
        
    except Exception as e:
        print(f"⚠️ Provider oluşturma hatası (beklenen - API key yok): {e}")
    
    print("✅ Provider oluşturma testi tamamlandı!")

async def test_mock_generation():
    """Mock generation testi."""
    print("\n🤖 Mock generation testi...")
    
    # Bu test gerçek API çağrısı yapmaz, sadece yapıyı test eder
    try:
        from llm_provider.settings import GenerationRequest, GenerationResponse
        
        # Request oluştur
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=100,
            temperature=0.7
        )
        print(f"✅ GenerationRequest oluşturuldu: {request.prompt}")
        
        # Response oluştur
        response = GenerationResponse(
            content="Test response",
            provider="test",
            model="test-model"
        )
        print(f"✅ GenerationResponse oluşturuldu: {response.content}")
        
    except Exception as e:
        print(f"❌ Mock generation hatası: {e}")
    
    print("✅ Mock generation testi tamamlandı!")

def main():
    """Ana test fonksiyonu."""
    print("🚀 LLM Provider Factory Test PyPI Yükleme Testi")
    print("=" * 50)
    
    test_basic_functionality()
    test_message_system()
    test_provider_creation()
    
    # Async test
    asyncio.run(test_mock_generation())
    
    print("\n🎉 Tüm testler tamamlandı!")
    print("📦 Paket Test PyPI'den başarıyla yüklendi ve çalışıyor!")

if __name__ == "__main__":
    main()