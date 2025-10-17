#!/usr/bin/env python3
"""
External Debug Test for VertexAI Provider
Bu dosyayı başka bir projede kullanarak debug edebilirsiniz
"""

import asyncio
import os
import sys
from pathlib import Path

def setup_external_debug():
    """External debug environment setup"""
    
    print("🔧 External Debug Setup")
    print("=" * 50)
    
    # 1. Package installation check
    try:
        from llm_provider import LLMProviderFactory
        from llm_provider.utils.config import VertexAIConfig
        from llm_provider.settings import GenerationRequest, Message, MessageRole
        print("✅ llm-provider-factory package imported successfully")
    except ImportError as e:
        print(f"❌ Package import failed: {e}")
        print("💡 Install with: pip install llm-provider-factory==0.2.0")
        return False
    
    # 2. Environment variables check
    required_vars = {
        'GOOGLE_APPLICATION_CREDENTIALS': 'Path to service account JSON',
        'GOOGLE_CLOUD_PROJECT': 'Your Google Cloud Project ID'
    }
    
    missing_vars = []
    for var, desc in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"  {var}: {desc}")
    
    if missing_vars:
        print("⚠️ Missing environment variables:")
        for var in missing_vars:
            print(var)
        print("\n💡 Set them with:")
        print("export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account.json'")
        print("export GOOGLE_CLOUD_PROJECT='your-project-id'")
        return False
    
    print("✅ Environment variables configured")
    return True

async def test_basic_functionality():
    """Test basic VertexAI functionality"""
    
    print("\n🧪 Basic Functionality Test")
    print("=" * 50)
    
    try:
        # Config from environment
        config = VertexAIConfig(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location="us-central1",
            model="gemini-1.5-flash",  # Safe, fast model
            temperature=0.7,
            max_tokens=200
        )
        
        print(f"📋 Config: {config.project_id}, {config.model}")
        
        # Create provider
        factory = LLMProviderFactory()
        provider = factory.create_provider("vertexai", config)
        
        # Provider info
        info = provider.get_provider_info()
        print(f"✅ Provider: {info.display_name}")
        print(f"📊 Supported Models: {len(info.supported_models)}")
        print(f"🎯 Mistral Support: {'mistral-large-2411' in info.supported_models}")
        
        # Availability check
        print(f"🟢 Available: {provider.is_available()}")
        
        return provider
        
    except Exception as e:
        print(f"❌ Basic test failed: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_simple_generation(provider):
    """Test simple text generation"""
    
    print("\n💬 Simple Generation Test")
    print("=" * 50)
    
    try:
        request = GenerationRequest(
            messages=[
                Message(role=MessageRole.SYSTEM, content="Sen kısa ve net cevaplar veren yardımcı bir asistansın."),
                Message(role=MessageRole.USER, content="Merhaba! Kendini tanıt.")
            ],
            max_tokens=100,
            temperature=0.5
        )
        
        print("🚀 Generating response...")
        response = await provider.generate(request)
        
        print(f"✅ Response received!")
        print(f"📝 Content: {response.content}")
        print(f"🤖 Model: {response.model}")
        print(f"📊 Usage: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ Generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_mistral_model(provider):
    """Test Mistral model specifically"""
    
    print("\n🎭 Mistral Model Test")
    print("=" * 50)
    
    try:
        # Create Mistral config
        mistral_config = VertexAIConfig(
            project_id=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location="us-central1",
            model="mistral-large-2411",  # Mistral model
            temperature=0.3,
            max_tokens=150
        )
        
        factory = LLMProviderFactory()
        mistral_provider = factory.create_provider("vertexai", mistral_config)
        
        request = GenerationRequest(
            messages=[
                Message(role=MessageRole.USER, content="Explain machine learning in one sentence.")
            ],
            max_tokens=50
        )
        
        print("🎯 Testing Mistral model...")
        response = await mistral_provider.generate(request)
        
        print(f"✅ Mistral response: {response.content}")
        print(f"🤖 Model used: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"⚠️ Mistral test failed (might fallback to Gemini): {e}")
        # This is expected if Mistral is not available
        return False

async def test_conversation_history(provider):
    """Test conversation with history"""
    
    print("\n💭 Conversation History Test")
    print("=" * 50)
    
    try:
        # Multi-turn conversation
        conversation = [
            Message(role=MessageRole.SYSTEM, content="Sen yardımcı bir programlama asistanısın."),
            Message(role=MessageRole.USER, content="Python nedir?"),
            Message(role=MessageRole.ASSISTANT, content="Python bir programlama dilidir."),
            Message(role=MessageRole.USER, content="Python'un avantajları nelerdir?")
        ]
        
        request = GenerationRequest(
            messages=conversation,
            max_tokens=150,
            temperature=0.6
        )
        
        print("💬 Testing conversation with history...")
        response = await provider.generate(request)
        
        print(f"✅ Conversation response: {response.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Conversation test failed: {e}")
        return False

async def test_streaming(provider):
    """Test streaming generation"""
    
    print("\n🌊 Streaming Test")
    print("=" * 50)
    
    try:
        request = GenerationRequest(
            messages=[
                Message(role=MessageRole.USER, content="Write a short poem about AI.")
            ],
            max_tokens=100
        )
        
        print("🔄 Starting streaming...")
        chunks = []
        async for chunk in provider.stream_generate(request):
            chunks.append(chunk.content)
            print(f"📦 Chunk: {chunk.content}", end="", flush=True)
        
        print(f"\n✅ Streaming completed! Received {len(chunks)} chunks")
        
        return True
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return False

async def main():
    """Main debug function"""
    
    print("🚀 VertexAI Provider External Debug")
    print("=" * 50)
    
    # Setup check
    if not setup_external_debug():
        print("\n❌ Setup failed. Please fix the issues above.")
        return
    
    # Basic functionality
    provider = await test_basic_functionality()
    if not provider:
        print("\n❌ Cannot continue without a working provider.")
        return
    
    # Test suite
    tests = [
        ("Simple Generation", test_simple_generation),
        ("Mistral Model", test_mistral_model),
        ("Conversation History", test_conversation_history),
        ("Streaming", test_streaming),
    ]
    
    results = []
    for test_name, test_func in tests:
        if test_name == "Mistral Model":
            # Optional test
            result = await test_func(provider)
            results.append((test_name, result, True))  # Optional
        else:
            result = await test_func(provider)
            results.append((test_name, result, False))  # Required
    
    # Results summary
    print("\n📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result, optional in results:
        status = "✅ PASS" if result else ("⚠️ SKIP" if optional else "❌ FAIL")
        print(f"{status} {test_name}")
        
        if result:
            passed += 1
        elif not optional:
            failed += 1
    
    print(f"\n🏆 Final Score: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All critical tests passed! VertexAI provider is working correctly.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")

if __name__ == "__main__":
    # Usage instructions
    print("💡 Usage Instructions:")
    print("1. Install: pip install llm-provider-factory==0.2.0")
    print("2. Set environment variables:")
    print("   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/service-account.json'")
    print("   export GOOGLE_CLOUD_PROJECT='your-project-id'")
    print("3. Run: python external_debug.py")
    print()
    
    asyncio.run(main())