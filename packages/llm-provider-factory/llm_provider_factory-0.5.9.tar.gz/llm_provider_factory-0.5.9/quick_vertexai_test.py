#!/usr/bin/env python3
"""
Quick VertexAI Model Test - Hangi modeller çalışıyor test et
"""
import asyncio
import os
from google.cloud import aiplatform
from vertexai.generative_models import GenerativeModel

# Google Cloud credentials - dosyanın başında manuel olarak girin
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/Users/sadikhanecioglu/Projects/LiveKitAgentSample/sample/src/service-account.json"

PROJECT_ID = "api-project-104525573244"
LOCATION = "us-central1"

async def test_model(model_name: str):
    """Test a specific model."""
    try:
        print(f"\n🧪 Testing {model_name}...")
        
        # Initialize Vertex AI
        aiplatform.init(project=PROJECT_ID, location=LOCATION)
        
        # Create model
        model = GenerativeModel(model_name)
        
        # Simple test
        response = model.generate_content("Hello, world!")
        
        print(f"✅ {model_name} çalışıyor!")
        print(f"   Response: {response.text[:100]}...")
        return True
        
    except Exception as e:
        print(f"❌ {model_name} hatası: {e}")
        return False

async def main():
    """Test different models."""
    print("🚀 VertexAI Model Test")
    print(f"📁 Project: {PROJECT_ID}")
    print(f"📍 Location: {LOCATION}")
    
    # Test different models
    models_to_test = [
        "gemini-pro",
        "gemini-1.0-pro", 
        "text-bison",
        "chat-bison",
        "text-bison@001",
        "chat-bison@001",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    working_models = []
    
    for model in models_to_test:
        if await test_model(model):
            working_models.append(model)
        await asyncio.sleep(1)  # Rate limit
    
    print(f"\n📊 Results:")
    print(f"✅ Working models: {working_models}")
    print(f"❌ Failed models: {len(models_to_test) - len(working_models)}")

if __name__ == "__main__":
    asyncio.run(main())