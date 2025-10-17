#!/usr/bin/env python3
"""
🦙 Ollama Provider Kullanım Örnekleri
Local LLM'leri nasıl kullanacağınızı gösterir
"""

import asyncio
from llm_provider import LLMProviderFactory
from llm_provider.utils.config import OllamaConfig
from llm_provider.settings import GenerationRequest, Message, MessageRole


async def basic_ollama_example():
    """🧪 Temel Ollama Kullanımı"""
    print("🦙 Temel Ollama Örneği")
    print("=" * 40)
    
    # 1. Config oluştur
    config = OllamaConfig(
        base_url="http://localhost:11434",  # Ollama server
        model="llama3.1:latest",           # Kullanılacak model
        max_tokens=150,
        temperature=0.7
    )
    
    # 2. Provider oluştur
    factory = LLMProviderFactory()
    provider = factory.create_provider("ollama", config)
    
    # 3. Basit soru sor
    request = GenerationRequest(
        prompt="Python nedir? Kısa açıkla.",
        max_tokens=100,
        temperature=0.7
    )
    
    response = await provider.generate(request)
    print(f"🤖 Cevap: {response.content}")
    print(f"⏱️ Süre: {response.usage.total_time:.2f}s" if response.usage else "")


async def conversation_example():
    """💬 Konversasyon Örneği"""
    print("\n💬 Konversasyon Örneği")
    print("=" * 40)
    
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3.1:latest",
        max_tokens=200,
        temperature=0.8
    )
    
    factory = LLMProviderFactory()
    provider = factory.create_provider("ollama", config)
    
    # Konversasyon geçmişi
    messages = [
        Message(role=MessageRole.USER, content="Merhaba! Ben Python öğreniyorum."),
        Message(role=MessageRole.ASSISTANT, content="Merhaba! Python öğrenmen harika. Hangi konularda yardım edebilirim?"),
        Message(role=MessageRole.USER, content="Liste comprehension nasıl kullanılır?")
    ]
    
    request = GenerationRequest(
        messages=messages,
        max_tokens=200,
        temperature=0.8
    )
    
    response = await provider.generate(request)
    print(f"🤖 AI Yanıtı: {response.content}")


async def streaming_example():
    """📡 Streaming Örneği"""
    print("\n📡 Streaming Örneği")
    print("=" * 40)
    
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3.1:latest",
        max_tokens=300,
        temperature=0.9
    )
    
    factory = LLMProviderFactory()
    provider = factory.create_provider("ollama", config)
    
    request = GenerationRequest(
        prompt="Yapay zeka hakkında kısa bir hikaye yaz.",
        max_tokens=300,
        temperature=0.9
    )
    
    print("🤖 AI Hikayesi (Canlı): ", end="", flush=True)
    
    full_response = ""
    chunk_count = 0
    
    async for chunk in provider.stream_generate(request):
        print(chunk.content, end="", flush=True)
        full_response += chunk.content
        chunk_count += 1
    
    print(f"\n\n📊 {chunk_count} chunk alındı")
    print(f"📝 Toplam {len(full_response)} karakter")


async def multiple_models_example():
    """🔄 Çoklu Model Örneği"""
    print("\n🔄 Çoklu Model Karşılaştırması")
    print("=" * 40)
    
    models = ["llama3.1:latest", "llama2", "codellama"]
    prompt = "Hello world programını Python ile nasıl yazarım?"
    
    factory = LLMProviderFactory()
    
    for model in models:
        try:
            print(f"\n🧠 Model: {model}")
            print("-" * 20)
            
            config = OllamaConfig(
                base_url="http://localhost:11434",
                model=model,
                max_tokens=100,
                temperature=0.5
            )
            
            provider = factory.create_provider("ollama", config)
            
            request = GenerationRequest(
                prompt=prompt,
                max_tokens=100,
                temperature=0.5
            )
            
            response = await provider.generate(request)
            print(f"✅ Cevap: {response.content[:200]}...")
            
        except Exception as e:
            print(f"❌ {model} modeli kullanılamıyor: {e}")


async def code_generation_example():
    """💻 Kod Üretimi Örneği"""
    print("\n💻 Kod Üretimi Örneği")
    print("=" * 40)
    
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="codellama",  # Kod için özel model
        max_tokens=300,
        temperature=0.3  # Kod için düşük temperature
    )
    
    factory = LLMProviderFactory()
    
    try:
        provider = factory.create_provider("ollama", config)
        
        request = GenerationRequest(
            prompt="""
Bir Python fonksiyonu yaz:
- Fibonacci sayısı hesaplar
- Recursive ve iterative versiyonları olsun
- Docstring ekle
- Type hints kullan
""",
            max_tokens=300,
            temperature=0.3
        )
        
        response = await provider.generate(request)
        print("🤖 Üretilen Kod:")
        print("```python")
        print(response.content)
        print("```")
        
    except Exception as e:
        print(f"❌ CodeLlama modeli yok, llama3.1 ile deneyelim: {e}")
        
        # Fallback to llama3.1
        config.model = "llama3.1:latest"
        provider = factory.create_provider("ollama", config)
        response = await provider.generate(request)
        print("🤖 Üretilen Kod (llama3.1):")
        print("```python")
        print(response.content)
        print("```")


async def advanced_configuration_example():
    """⚙️ Gelişmiş Konfigürasyon"""
    print("\n⚙️ Gelişmiş Konfigürasyon")
    print("=" * 40)
    
    # Özel parametrelerle config
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3.1:latest",
        max_tokens=500,
        temperature=0.8,
        top_p=0.9,
        top_k=40,
        repeat_penalty=1.1
    )
    
    factory = LLMProviderFactory()
    provider = factory.create_provider("ollama", config)
    
    # Özel system prompt ile
    messages = [
        Message(
            role=MessageRole.SYSTEM, 
            content="Sen uzman bir Python geliştiricisisin. Açık ve detaylı örnekler verirsin."
        ),
        Message(
            role=MessageRole.USER, 
            content="Django ile REST API nasıl oluşturulur?"
        )
    ]
    
    request = GenerationRequest(
        messages=messages,
        max_tokens=500,
        temperature=0.8
    )
    
    response = await provider.generate(request)
    print(f"🤖 Uzman Cevabı: {response.content}")


async def error_handling_example():
    """🚨 Hata Yönetimi"""
    print("\n🚨 Hata Yönetimi Örneği")
    print("=" * 40)
    
    # Olmayan model ile test
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="nonexistent-model",
        max_tokens=100
    )
    
    factory = LLMProviderFactory()
    
    try:
        provider = factory.create_provider("ollama", config)
        
        request = GenerationRequest(
            prompt="Test prompt",
            max_tokens=100
        )
        
        response = await provider.generate(request)
        print(f"✅ Beklenmedik başarı: {response.content}")
        
    except Exception as e:
        print(f"❌ Beklenen hata yakalandı: {type(e).__name__}: {e}")
    
    # Yanlış server adresi
    config = OllamaConfig(
        base_url="http://localhost:99999",  # Yanlış port
        model="llama3.1:latest"
    )
    
    try:
        provider = factory.create_provider("ollama", config)
        request = GenerationRequest(prompt="Test", max_tokens=50)
        response = await provider.generate(request)
        
    except Exception as e:
        print(f"❌ Bağlantı hatası yakalandı: {type(e).__name__}: {e}")


async def main():
    """🎯 Ana fonksiyon - Tüm örnekleri çalıştır"""
    
    print("🦙 OLLAMA PROVIDER KULLANIM ÖRNEKLERİ")
    print("=" * 50)
    print("Önkoşul: Ollama server çalışıyor olmalı (localhost:11434)")
    print("Model indirme: ollama pull llama3.1:latest")
    print("=" * 50)
    
    try:
        await basic_ollama_example()
        await conversation_example()
        await streaming_example()
        await multiple_models_example()
        await code_generation_example()
        await advanced_configuration_example()
        await error_handling_example()
        
        print("\n🎉 Tüm örnekler tamamlandı!")
        print("💡 İpucu: Bu kodu geliştirerek kendi uygulamanızı yapabilirsiniz!")
        
    except Exception as e:
        print(f"\n❌ Genel hata: {e}")
        print("💡 Ollama server çalışıyor mu kontrol edin:")
        print("   curl http://localhost:11434/api/tags")


if __name__ == "__main__":
    asyncio.run(main())