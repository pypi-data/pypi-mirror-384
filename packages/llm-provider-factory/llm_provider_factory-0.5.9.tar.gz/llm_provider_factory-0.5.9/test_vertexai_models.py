#!/usr/bin/env python3
"""
VertexAI Provider Model Test - Working models test
"""
import asyncio
import os
import sys

# Add project to path
sys.path.insert(0, '/Users/sadikhanecioglu/Documents/Works/llmfactory-clean/src')

from llm_provider.providers.vertexai_provider import VertexAIProvider
from llm_provider.settings import GenerationRequest
from llm_provider.utils.config import VertexAIConfig

async def test_vertexai_model(model_name: str):
    """Test a specific VertexAI model."""
    try:
        print(f"\n🧪 Testing {model_name}...")
        
        # Create provider config
        config = VertexAIConfig(
            project_id="api-project-104525573244",
            location="us-central1",  # Back to us-central1
            model=model_name,
            credentials_path="/Users/sadikhanecioglu/Projects/LiveKitAgentSample/sample/src/service-account.json"
        )
        
        # Create provider
        provider = VertexAIProvider(config)
        
        # Test connection
        if not provider.is_available():
            print(f"❌ {model_name} provider not available")
            return False
        
        # Test generation
        request = GenerationRequest(prompt="Hello! Can you introduce yourself briefly?")
        response = await provider.generate(request)
        
        print(f"✅ {model_name} çalışıyor!")
        print(f"   Response: {response.content[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ {model_name} hatası: {str(e)[:200]}...")
        return False

async def main():
    """Test different VertexAI models."""
    print("🚀 VertexAI Provider Model Test")
    
    # Test different models with various naming conventions
    models_to_test = [
        "mistral-large-2411",
        "gemini-1.5-flash-001",
        "gemini-pro"
    ]
    
    working_models = []
    
    for model in models_to_test:
        if await test_vertexai_model(model):
            working_models.append(model)
        await asyncio.sleep(2)  # Rate limit
    
    print(f"\n📊 Results:")
    print(f"✅ Working models: {working_models}")
    print(f"❌ Failed models: {len(models_to_test) - len(working_models)}")
    
    if working_models:
        print(f"\n🎯 Use these models in your VertexAI provider config:")
        for model in working_models:
            print(f"   - {model}")

if __name__ == "__main__":
    asyncio.run(main())