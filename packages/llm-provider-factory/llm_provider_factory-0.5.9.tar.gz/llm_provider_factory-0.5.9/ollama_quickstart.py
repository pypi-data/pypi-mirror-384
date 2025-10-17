#!/usr/bin/env python3
"""
🚀 Ollama Quick Start - 5 Dakikada Başla!
"""

import asyncio
from llm_provider import LLMProviderFactory
from llm_provider.utils.config import OllamaConfig
from llm_provider.settings import GenerationRequest


async def quick_start():
    """5 dakikada Ollama kullanmaya başla!"""
    
    print("🦙 OLLAMA QUICK START")
    print("=" * 30)
    
    # ✅ 1. ADIM: Config oluştur
    config = OllamaConfig(
        base_url="http://localhost:11434",
        model="llama3.1:latest"
    )
    
    # ✅ 2. ADIM: Provider oluştur  
    factory = LLMProviderFactory()
    provider = factory.create_provider("ollama", config)
    
    # ✅ 3. ADIM: Soru sor
    request = GenerationRequest(
        prompt="Python ile web scraping nasıl yapılır?",
        max_tokens=200
    )
    
    # ✅ 4. ADIM: Cevabı al
    response = await provider.generate(request)
    print(f"🤖 Cevap: {response.content}")
    
    print("\n🎉 Başarılı! Artık Ollama kullanıyorsunuz!")


if __name__ == "__main__":
    asyncio.run(quick_start())