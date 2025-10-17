#!/usr/bin/env python3
"""
Interactive Image Generation Demo

Bu demo file'i ile image generation'ı interaktif olarak test edebilirsiniz.
API key'lerinizi environment variable olarak ayarlayın.

Kullanım:
    export OPENAI_API_KEY="sk-your-key"
    export REPLICATE_API_TOKEN="r8_your-token"  
    python demo_image_generation.py
"""

import asyncio
import sys
import os

# Local import
sys.path.insert(0, "src")

async def demo_openai():
    """OpenAI DALL-E demo"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    from llm_provider import ImageProviderFactory
    
    print("🎨 OpenAI DALL-E Demo")
    print("-" * 30)
    
    factory = ImageProviderFactory()
    provider = factory.create_openai_image(
        api_key=openai_key,
        model="dall-e-3",
        size="1024x1024"
    )
    
    prompt = input("📝 Enter your image prompt: ").strip()
    if not prompt:
        prompt = "A futuristic robot painting a masterpiece"
    
    print(f"🎨 Generating image: '{prompt}'")
    print("⏳ Please wait...")
    
    try:
        response = await provider.generate_image(prompt=prompt)
        print(f"✅ Success! Image URL: {response.urls[0]}")
        print(f"   Model: {response.model}")
        print(f"   Size: {response.size}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def demo_replicate():
    """Replicate demo"""
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    if not replicate_token:
        print("❌ REPLICATE_API_TOKEN not found")
        return
    
    from llm_provider import ImageProviderFactory
    
    print("🔄 Replicate SDXL Demo")
    print("-" * 30)
    
    factory = ImageProviderFactory()
    provider = factory.create_replicate_image(
        api_token=replicate_token,
        model="stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b"
    )
    
    prompt = input("📝 Enter your image prompt: ").strip()
    if not prompt:
        prompt = "A cyberpunk cityscape with neon lights"
    
    print(f"🎨 Generating image: '{prompt}'")
    print("⏳ Please wait...")
    
    try:
        response = await provider.generate_image(
            prompt=prompt,
            width=1024,
            height=1024,
            num_inference_steps=25
        )
        print(f"✅ Success! Image URL: {response.urls[0]}")
        print(f"   Model: {response.model}")
        print(f"   Size: {response.size}")
    except Exception as e:
        print(f"❌ Error: {e}")

async def demo_combined():
    """Combined LLM + Image demo"""
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        print("❌ OPENAI_API_KEY not found")
        return
    
    from llm_provider import LLMProviderFactory, ImageProviderFactory
    
    print("🤖 Combined LLM + Image Demo")
    print("-" * 35)
    
    topic = input("📝 Enter a topic for image prompt generation: ").strip()
    if not topic:
        topic = "magical forest"
    
    # Generate prompt with LLM
    print(f"🧠 Creating image prompt about '{topic}'...")
    llm_factory = LLMProviderFactory()
    llm = llm_factory.create_openai(api_key=openai_key)
    
    try:
        llm_response = await llm.generate(
            f"Create a detailed, artistic prompt for an AI image generator about {topic}. "
            f"Make it very descriptive and artistic, under 100 words."
        )
        
        generated_prompt = llm_response.content.strip()
        print(f"✅ Generated prompt: {generated_prompt}")
        
        # Generate image with the prompt
        print("🎨 Generating image with AI-created prompt...")
        image_factory = ImageProviderFactory()
        image_provider = image_factory.create_openai_image(api_key=openai_key)
        
        image_response = await image_provider.generate_image(prompt=generated_prompt)
        
        print(f"✅ Success! Image URL: {image_response.urls[0]}")
        print(f"   Final prompt used: {generated_prompt}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

async def main():
    """Main demo function"""
    print("🚀 Image Generation Interactive Demo")
    print("=" * 45)
    print()
    
    # Check API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    
    if not openai_key and not replicate_token:
        print("❌ No API keys found!")
        print("Please set environment variables:")
        print("   export OPENAI_API_KEY='sk-your-key'")
        print("   export REPLICATE_API_TOKEN='r8_your-token'")
        return
    
    options = []
    if openai_key:
        options.extend(["1. OpenAI DALL-E", "3. Combined LLM + Image"])
    if replicate_token:
        options.append("2. Replicate SDXL")
    options.append("0. Exit")
    
    while True:
        print("\nSelect demo:")
        for option in options:
            print(f"   {option}")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == "1" and openai_key:
            await demo_openai()
        elif choice == "2" and replicate_token:
            await demo_replicate()
        elif choice == "3" and openai_key:
            await demo_combined()
        elif choice == "0":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted")
    except Exception as e:
        print(f"\n💥 Error: {e}")