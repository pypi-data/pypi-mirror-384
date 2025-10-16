#!/usr/bin/env python3
"""
Test script for VertexAI with Mistral model
Bu script sizin orijinal yaklaşımınızı test eder
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the src directory to the path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from llm_provider import LLMProviderFactory
from llm_provider.utils.config import VertexAIConfig

async def test_mistral_with_vertexai():
    """Test Mistral model with VertexAI"""
    
    print("🧪 VertexAI Mistral Test Başlıyor...")
    
    # Configuration
    config = VertexAIConfig(
        project_id="your-project-id",  # Gerçek project ID'nizi buraya yazın
        location="us-central1",
        model="mistral-large-2411",
        credentials_path="/path/to/your/credentials.json",  # Gerçek credentials path'ini yazın
        temperature=0.1,
        max_tokens=1000
    )
    
    try:
        # Create factory
        factory = LLMProviderFactory()
        
        # Create provider
        provider = factory.create_provider("vertexai", config)
        
        print(f"✅ Provider oluşturuldu: {provider.get_provider_info().display_name}")
        
        # Test basic response
        test_prompt = "Merhaba! Sen kimsin ve nasıl yardım edebilirsin?"
        
        print(f"📝 Test prompt: {test_prompt}")
        
        # Check availability
        if not provider.is_available():
            print("❌ Provider kullanılamıyor")
            return
        
        # Generate response
        from llm_provider.settings import GenerationRequest, Message, MessageRole
        
        request = GenerationRequest(
            messages=[
                Message(role=MessageRole.SYSTEM, content="Sen yardımcı bir AI asistanısın. Türkçe cevap ver."),
                Message(role=MessageRole.USER, content=test_prompt)
            ],
            max_tokens=500,
            temperature=0.1
        )
        
        print("🚀 Cevap oluşturuluyor...")
        response = await provider.generate(request)
        
        print(f"✅ Cevap alındı!")
        print(f"Model: {response.model}")
        print(f"İçerik: {response.content}")
        print(f"Kullanım: {response.usage}")
        
        # Test conversation history
        print("\n🔄 Conversation history testi...")
        
        history_request = GenerationRequest(
            messages=[
                Message(role=MessageRole.SYSTEM, content="Sen yardımcı bir AI asistanısın."),
                Message(role=MessageRole.USER, content="Python hakkında bir şey sor"),
                Message(role=MessageRole.ASSISTANT, content="Python hangi alanda kullanmak istiyorsun?"),
                Message(role=MessageRole.USER, content="Web geliştirme için")
            ],
            max_tokens=300,
            temperature=0.1
        )
        
        history_response = await provider.generate(history_request)
        print(f"✅ History cevabı: {history_response.content}")
        
    except Exception as e:
        print(f"❌ Hata oluştu: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🔧 VertexAI + Mistral Test")
    print("⚠️  Önce credentials ve project ID'yi güncelleyin!")
    
    # Check if configuration is updated
    if "your-project-id" in open(__file__).read():
        print("❌ Lütfen test scriptindeki 'your-project-id' ve credentials path'ini güncelleyin")
        sys.exit(1)
    
    asyncio.run(test_mistral_with_vertexai())