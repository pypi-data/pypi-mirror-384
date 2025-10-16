#!/usr/bin/env python3
"""
Quick Image Provider Test

Bu test sadece temel functionality'i kontrol eder.
Gerçek API çağrısı yapmaz, sadece provider'ların doğru çalıştığını test eder.

Kullanım:
    python quick_image_test.py
"""

import asyncio
import sys
import os

# Local import
sys.path.insert(0, "src")

def test_imports():
    """Test basic imports"""
    print("🧪 Testing Imports")
    print("-" * 20)
    
    try:
        from llm_provider import ImageProviderFactory
        print("✅ ImageProviderFactory import successful")
    except ImportError as e:
        print(f"❌ ImageProviderFactory import failed: {e}")
        return False
    
    try:
        from llm_provider import LLMProviderFactory
        print("✅ LLMProviderFactory import successful")
    except ImportError as e:
        print(f"❌ LLMProviderFactory import failed: {e}")
        return False
    
    return True

def test_factory_creation():
    """Test factory creation"""
    print("\n🏭 Testing Factory Creation")
    print("-" * 30)
    
    try:
        from llm_provider import ImageProviderFactory
        factory = ImageProviderFactory()
        print("✅ ImageProviderFactory created successfully")
        
        providers = factory.get_available_providers()
        print(f"✅ Available providers: {list(providers.keys())}")
        
        return True, factory
    except Exception as e:
        print(f"❌ Factory creation failed: {e}")
        return False, None

def test_provider_methods(factory):
    """Test provider creation methods"""
    print("\n🔧 Testing Provider Methods")
    print("-" * 30)
    
    success = True
    
    # Test OpenAI method
    try:
        openai_provider = factory.create_openai_image(
            api_key="dummy-key-for-testing"
        )
        print("✅ OpenAI provider creation method works")
    except Exception as e:
        print(f"❌ OpenAI provider creation failed: {e}")
        success = False
    
    # Test Replicate method
    try:
        replicate_provider = factory.create_replicate_image(
            api_token="dummy-token-for-testing"
        )
        print("✅ Replicate provider creation method works")
    except Exception as e:
        print(f"❌ Replicate provider creation failed: {e}")
        success = False
    
    return success

async def test_basic_api_call():
    """Test a basic API call if keys are available"""
    print("\n🌐 Testing Basic API Call")
    print("-" * 30)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_key:
        print("⏭️  No OPENAI_API_KEY found - skipping API test")
        print("   Set OPENAI_API_KEY to test real API calls")
        return True
    
    try:
        from llm_provider import ImageProviderFactory
        
        factory = ImageProviderFactory()
        provider = factory.create_openai_image(
            api_key=openai_key,
            model="dall-e-3"
        )
        
        print("📝 Making real API call: 'A simple test image'")
        response = await provider.generate_image(
            prompt="A simple geometric pattern, minimalist design",
            size="1024x1024",
            quality="standard"
        )
        
        print(f"✅ API call successful!")
        print(f"   Model: {response.model}")
        print(f"   Size: {response.size}")
        print(f"   Image URL: {response.urls[0][:60]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

async def main():
    """Main test function"""
    print("🚀 Quick Image Provider Test")
    print("=" * 40)
    
    # Test imports
    if not test_imports():
        print("\n💥 Import tests failed - cannot continue")
        sys.exit(1)
    
    # Test factory creation
    success, factory = test_factory_creation()
    if not success:
        print("\n💥 Factory creation failed - cannot continue")
        sys.exit(1)
    
    # Test provider methods
    if not test_provider_methods(factory):
        print("\n⚠️  Some provider method tests failed")
    
    # Test basic API call
    await test_basic_api_call()
    
    print("\n🎉 Quick tests completed!")
    print("\nℹ️  For comprehensive testing with real APIs:")
    print("   export OPENAI_API_KEY='your-key'")
    print("   export REPLICATE_API_TOKEN='your-token'")
    print("   python test_image_providers_real.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        sys.exit(1)