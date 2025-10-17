#!/usr/bin/env python3
"""
Quick Test Script for VertexAI Provider
Hem internal hem external debug için kullanılabilir
"""

import asyncio
import os
import sys

# Add current directory to path for internal testing
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, 'src')
if os.path.exists(src_dir):
    sys.path.insert(0, src_dir)

def test_internal():
    """Internal testing (development mode)"""
    print("🏠 Internal Testing Mode")
    
    try:
        # Import from local source
        from llm_provider.utils.config import VertexAIConfig
        from llm_provider.providers.vertexai_provider import VertexAIProvider
        from llm_provider import LLMProviderFactory
        
        print("✅ Local imports successful")
        
        # Quick test
        config = VertexAIConfig(
            project_id="test-project",
            model="gemini-1.5-flash"
        )
        
        provider = VertexAIProvider(config)
        info = provider.get_provider_info()
        
        print(f"✅ Provider: {info.display_name}")
        print(f"📋 Models: {len(info.supported_models)}")
        print(f"🎯 Mistral: {'mistral' in str(info.supported_models)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Internal test failed: {e}")
        return False

def test_external():
    """External testing (package mode)"""
    print("🌍 External Testing Mode")
    
    try:
        # Import from installed package
        from llm_provider import LLMProviderFactory
        from llm_provider.utils.config import VertexAIConfig
        
        print("✅ Package imports successful")
        
        # Quick test
        factory = LLMProviderFactory()
        available = factory.get_available_providers()
        
        print(f"✅ Available providers: {available}")
        print(f"🎯 VertexAI available: {'vertexai' in available}")
        
        if 'vertexai' in available:
            config = VertexAIConfig(
                project_id="test-project",
                model="gemini-1.5-flash"
            )
            
            provider = factory.create_provider("vertexai", config)
            info = provider.get_provider_info()
            
            print(f"✅ VertexAI Provider: {info.display_name}")
            print(f"📋 Supported models: {len(info.supported_models)}")
        
        return True
        
    except Exception as e:
        print(f"❌ External test failed: {e}")
        return False

async def test_real_generation():
    """Test real generation (requires credentials)"""
    print("\n🚀 Real Generation Test")
    
    # Check credentials
    if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
        print("⚠️ No credentials - skipping real test")
        print("💡 Set GOOGLE_APPLICATION_CREDENTIALS to test with real API")
        return False
    
    if not os.getenv("GOOGLE_CLOUD_PROJECT"):
        print("⚠️ No project ID - skipping real test")
        print("💡 Set GOOGLE_CLOUD_PROJECT to test with real API")
        return False
    
    try:
        from llm_provider import LLMProviderFactory
        from llm_provider.utils.config import VertexAIConfig
        from llm_provider.settings import GenerationRequest, Message, MessageRole
        
        config = VertexAIConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT"),
            model="gemini-1.5-flash",
            max_tokens=50
        )
        
        factory = LLMProviderFactory()
        provider = factory.create_provider("vertexai", config)
        
        request = GenerationRequest(
            messages=[
                Message(role=MessageRole.USER, content="Say hello in one word")
            ]
        )
        
        print("🔄 Generating with real API...")
        response = await provider.generate(request)
        
        print(f"✅ Real response: {response.content}")
        print(f"🤖 Model: {response.model}")
        
        return True
        
    except Exception as e:
        print(f"❌ Real generation failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 VertexAI Provider Quick Test")
    print("=" * 40)
    
    # Determine test mode
    is_development = os.path.exists(os.path.join(current_dir, 'src', 'llm_provider'))
    
    if is_development:
        print("🏠 Development environment detected")
        success = test_internal()
    else:
        print("📦 Package environment detected")
        success = test_external()
    
    if success:
        print("\n✅ Basic tests passed!")
        
        # Try real generation if possible
        if asyncio.run(test_real_generation()):
            print("🎉 All tests passed including real API!")
        else:
            print("🎯 Basic tests passed (real API not tested)")
    else:
        print("\n❌ Basic tests failed!")
    
    print("\n📋 Debug Tips:")
    print("• Internal development: Run from project root")
    print("• External package: pip install llm-provider-factory==0.2.0")
    print("• Real API testing: Set GOOGLE_APPLICATION_CREDENTIALS and GOOGLE_CLOUD_PROJECT")

if __name__ == "__main__":
    main()