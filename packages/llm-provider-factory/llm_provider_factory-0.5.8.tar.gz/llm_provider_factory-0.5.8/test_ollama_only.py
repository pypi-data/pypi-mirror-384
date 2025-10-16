#!/usr/bin/env python3
"""
🦙 Ollama Provider Test - Local LLM Testing
Sadece Ollama provider'ını test eder
"""

import asyncio
import os
import time
from llm_provider import LLMProviderFactory
from llm_provider.utils.config import OllamaConfig
from llm_provider.settings import GenerationRequest


async def test_ollama():
    """Ollama provider'ını test et"""
    
    print("🦙 Ollama Provider Test")
    print("=" * 50)
    
    # Ollama server kontrolü
    ollama_url = "http://localhost:11434"
    print(f"🔗 Ollama URL: {ollama_url}")
    
    try:
        # Config oluştur
        config = OllamaConfig(
            base_url=ollama_url,
            model="llama3.1:latest",
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"📦 Model: {config.model}")
        print(f"🎛️ Max tokens: {config.max_tokens}")
        print(f"🌡️ Temperature: {config.temperature}")
        
        # Provider oluştur
        factory = LLMProviderFactory()
        provider = factory.create_provider("ollama", config)
        
        print("\n🧪 Test 1: Basic Generation")
        print("-" * 30)
        
        # Test isteği
        request = GenerationRequest(
            prompt="Merhaba! Sen kimsin? Çok kısa cevap ver.",
            max_tokens=100,
            temperature=0.7
        )
        
        start_time = time.time()
        response = await provider.generate(request)
        duration = time.time() - start_time
        
        print(f"✅ Başarılı! ({duration:.2f}s)")
        print(f"💬 Cevap: {response.content}")
        
        print("\n🧪 Test 2: Conversation")
        print("-" * 30)
        
        # Konversasyon testi
        conv_request = GenerationRequest(
            prompt="Python hakkında 2 cümle söyle.",
            max_tokens=80,
            temperature=0.5
        )
        
        start_time = time.time()
        conv_response = await provider.generate(conv_request)
        duration = time.time() - start_time
        
        print(f"✅ Başarılı! ({duration:.2f}s)")
        print(f"💬 Cevap: {conv_response.content}")
        
        print("\n🧪 Test 3: Streaming")
        print("-" * 30)
        
        # Streaming test
        stream_request = GenerationRequest(
            prompt="AI hakkında bir şiir yaz. Kısa olsun.",
            max_tokens=120,
            temperature=0.8
        )
        
        start_time = time.time()
        
        print("📡 Streaming başlıyor...")
        chunks = []
        async for chunk in provider.stream_generate(stream_request):
            chunks.append(chunk.content)
            print(f"📦 Chunk: {chunk.content}", end="", flush=True)
        
        duration = time.time() - start_time
        full_response = "".join(chunks)
        
        print(f"\n✅ Streaming tamamlandı! ({duration:.2f}s)")
        print(f"📊 {len(chunks)} chunk alındı")
        print(f"💬 Tam cevap: {full_response}")
        
        print("\n🎉 Tüm Ollama testleri başarılı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        print(f"📝 Hata türü: {type(e).__name__}")
        
        # Ollama server kontrol önerisi
        print("\n💡 Çözüm önerileri:")
        print("1. Ollama server çalışıyor mu kontrol edin:")
        print("   curl http://localhost:11434/api/tags")
        print("2. llama3.1:latest modeli yüklü mü kontrol edin:")
        print("   ollama list")
        print("3. Model yoksa indirin:")
        print("   ollama pull llama3.1:latest")


if __name__ == "__main__":
    asyncio.run(test_ollama())