#!/usr/bin/env python3
"""
Test script for VertexAI provider
"""
import asyncio
import os
from llm_provider import LLMProviderFactory, VertexAI, VertexAIConfig, Message, MessageRole


async def test_vertexai_basic():
    """Test basic VertexAI functionality."""
    print("=== Testing VertexAI Provider ===")
    
    # Create VertexAI configuration
    config = VertexAIConfig(
        project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id"),
        location="us-central1",
        model="gemini-pro"
    )
    
    # Create provider
    provider = VertexAI(config=config)
    factory = LLMProviderFactory(provider)
    
    try:
        print("Testing basic generation...")
        response = await factory.generate("Hello! Tell me about AI in 2 sentences.")
        print(f"Response: {response.content}")
        print(f"Model: {response.model}")
        if response.usage:
            print(f"Usage: {response.usage}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")
    
    print()


async def test_vertexai_conversation():
    """Test VertexAI with conversation history."""
    print("=== Testing VertexAI Conversation ===")
    
    # Create using factory convenience method
    factory = LLMProviderFactory.create_vertexai(
        config=VertexAIConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id"),
            location="us-central1"
        )
    )
    
    history = [
        Message(role=MessageRole.USER, content="What is Python?"),
        Message(role=MessageRole.ASSISTANT, content="Python is a high-level programming language known for its simplicity and readability."),
        Message(role=MessageRole.USER, content="What makes it popular?")
    ]
    
    try:
        response = await factory.generate(
            "Give me 3 specific reasons",
            history=history,
            max_tokens=200
        )
        print(f"Response: {response.content}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def test_vertexai_streaming():
    """Test VertexAI streaming."""
    print("=== Testing VertexAI Streaming ===")
    
    factory = LLMProviderFactory.create_vertexai(
        config=VertexAIConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id"),
            location="us-central1"
        )
    )
    
    try:
        print("Streaming response:")
        content = ""
        chunk_count = 0
        
        async for chunk in factory.stream_generate(
            "Write a short poem about machine learning",
            max_tokens=100
        ):
            if chunk.content:
                print(chunk.content, end="", flush=True)
                content += chunk.content
                chunk_count += 1
            
            if chunk.is_final:
                print(f"\n\nStream finished!")
                print(f"Total chunks: {chunk_count}")
                print(f"Total content length: {len(content)} characters")
                break
                
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def test_vertexai_models():
    """Test different VertexAI models."""
    print("=== Testing Different VertexAI Models ===")
    
    models = ["gemini-pro", "text-bison-001"]
    
    for model in models:
        print(f"\n--- Testing {model} ---")
        
        config = VertexAIConfig(
            project_id=os.getenv("GOOGLE_CLOUD_PROJECT", "your-project-id"),
            location="us-central1",
            model=model
        )
        
        factory = LLMProviderFactory.create_vertexai(config=config)
        
        try:
            response = await factory.generate(
                "What is the capital of France?",
                max_tokens=50
            )
            print(f"Response: {response.content}")
            print(f"Model used: {response.model}")
            
        except Exception as e:
            print(f"Error with {model}: {e}")
    
    print()


async def test_provider_info():
    """Test provider information."""
    print("=== Testing Provider Information ===")
    
    factory = LLMProviderFactory()
    
    try:
        providers = factory.get_available_providers()
        print(f"Available providers: {providers}")
        
        if "vertexai" in providers:
            info = factory.get_provider_info("vertexai")
            print(f"\nVertexAI Provider Info:")
            print(f"  Display Name: {info.display_name}")
            print(f"  Description: {info.description}")
            print(f"  Available: {info.is_available}")
            print(f"  Models: {info.supported_models[:5]}")  # First 5 models
            print(f"  Capabilities: {info.capabilities}")
        
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def main():
    """Run all tests."""
    print("Starting VertexAI Provider Tests...")
    print("Note: Set GOOGLE_CLOUD_PROJECT environment variable for actual testing")
    print("=" * 60)
    
    await test_provider_info()
    await test_vertexai_basic()
    await test_vertexai_conversation()
    await test_vertexai_streaming()
    await test_vertexai_models()
    
    print("All tests completed!")


if __name__ == "__main__":
    asyncio.run(main())