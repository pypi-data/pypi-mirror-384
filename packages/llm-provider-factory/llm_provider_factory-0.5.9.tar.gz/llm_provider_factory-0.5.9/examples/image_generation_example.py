"""
Image Generation Example

Bu örnek, LLM Provider Factory'nin image generation özelliklerini gösterir.
OpenAI DALL-E ve Replicate ile resim oluşturma işlemlerini örnekler.
"""

import asyncio
import os
from typing import Optional

from llm_provider import ImageProviderFactory, config_manager


async def openai_image_example():
    """OpenAI DALL-E ile resim oluşturma örneği"""
    print("🎨 OpenAI DALL-E Resim Oluşturma Örneği")
    print("=" * 50)
    
    try:
        # Image factory oluştur
        factory = ImageProviderFactory()
        
        # OpenAI image provider oluştur
        openai_provider = factory.create_openai_image(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        # Basit resim oluşturma
        print("📝 Prompt: 'A futuristic city with flying cars at sunset'")
        response = await openai_provider.generate_image(
            prompt="A futuristic city with flying cars at sunset",
            size="1024x1024",
            quality="standard"
        )
        
        print(f"✅ Resim oluşturuldu!")
        print(f"📍 URL: {response.urls[0]}")
        print(f"⚙️ Model: {response.model}")
        print(f"📏 Boyut: {response.size}")
        print(f"⏱️ Süre: {response.created_at}")
        print()
        
        # DALL-E 3 ile yüksek kalite
        print("📝 DALL-E 3 ile yüksek kalite resim:")
        response_hd = await openai_provider.generate_image(
            prompt="A majestic dragon soaring through clouds, digital art",
            model="dall-e-3",
            size="1024x1792",  # Portrait format
            quality="hd",
            style="vivid"
        )
        
        print(f"✅ HD Resim oluşturuldu!")
        print(f"📍 URL: {response_hd.urls[0]}")
        print(f"🎨 Stil: vivid")
        print(f"📐 Format: Portrait (1024x1792)")
        print()
        
    except Exception as e:
        print(f"❌ Hata: {e}")


async def replicate_image_example():
    """Replicate ile resim oluşturma örneği"""
    print("🔄 Replicate Resim Oluşturma Örneği")
    print("=" * 50)
    
    try:
        # Replicate provider oluştur
        factory = ImageProviderFactory()
        replicate_provider = factory.create_replicate_image(
            api_token=os.getenv("REPLICATE_API_TOKEN")
        )
        
        # Stable Diffusion ile basit resim
        print("📝 Prompt: 'A cyberpunk street scene with neon lights'")
        response = await replicate_provider.generate_image(
            prompt="A cyberpunk street scene with neon lights, 4k, detailed",
            model="stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
            width=1024,
            height=1024,
            num_inference_steps=50
        )
        
        print(f"✅ Resim oluşturuldu!")
        print(f"📍 URL: {response.urls[0]}")
        print(f"⚙️ Model: Stable Diffusion XL")
        print(f"📏 Boyut: 1024x1024")
        print()
        
        # Reference image ile stil aktarımı (örnek)
        print("📝 Reference image ile stil aktarımı:")
        # Not: Gerçek kullanımda reference_image URL'i sağlanmalı
        print("(Bu örnek reference image olmadan çalışır)")
        
        response_styled = await replicate_provider.generate_image(
            prompt="A portrait of a person in the style of Van Gogh",
            model="tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4",
            width=512,
            height=512,
            # reference_image="https://example.com/reference.jpg"  # Gerçek URL kullanın
        )
        
        print(f"✅ Stilli resim oluşturuldu!")
        print(f"📍 URL: {response_styled.urls[0]}")
        print()
        
    except Exception as e:
        print(f"❌ Hata: {e}")


async def combined_example():
    """Text ve Image generation kombinasyonu"""
    print("🤖 Kombine Metin ve Resim Oluşturma")
    print("=" * 50)
    
    try:
        # Önce text LLM ile resim promptu oluştur
        from llm_provider import LLMProviderFactory
        
        llm_factory = LLMProviderFactory()
        llm_provider = llm_factory.create_openai(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("📝 LLM'den resim promptu alınıyor...")
        text_response = await llm_provider.generate(
            "Create a detailed, artistic prompt for an AI image generator. "
            "The prompt should describe a beautiful fantasy landscape with magical elements. "
            "Keep it under 100 words and make it very descriptive."
        )
        
        generated_prompt = text_response.content
        print(f"🎨 Oluşturulan prompt: {generated_prompt}")
        print()
        
        # Bu promptu kullanarak resim oluştur
        image_factory = ImageProviderFactory()
        image_provider = image_factory.create_openai_image(
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("🖼️ Prompt kullanılarak resim oluşturuluyor...")
        image_response = await image_provider.generate_image(
            prompt=generated_prompt,
            size="1024x1024",
            quality="standard"
        )
        
        print(f"✅ Resim başarıyla oluşturuldu!")
        print(f"📍 URL: {image_response.urls[0]}")
        print(f"🎯 Bu workflow ile metin ve resim AI'ını birlikte kullanabilirsiniz!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")


async def main():
    """Ana fonksiyon - tüm örnekleri çalıştır"""
    print("🚀 LLM Provider Factory - Image Generation Örnekleri")
    print("=" * 70)
    print()
    
    # Environment variable kontrolü
    openai_key = os.getenv("OPENAI_API_KEY")
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    
    if not openai_key:
        print("⚠️  OPENAI_API_KEY environment variable bulunamadı!")
        print("   OpenAI örnekleri atlanacak.")
        print()
    
    if not replicate_token:
        print("⚠️  REPLICATE_API_TOKEN environment variable bulunamadı!")
        print("   Replicate örnekleri atlanacak.")
        print()
    
    # OpenAI örneği
    if openai_key:
        await openai_image_example()
        print()
    
    # Replicate örneği  
    if replicate_token:
        await replicate_image_example()
        print()
    
    # Kombine örnek
    if openai_key:
        await combined_example()
        print()
    
    print("🎉 Tüm örnekler tamamlandı!")
    print()
    print("💡 İpuçları:")
    print("   - API anahtarlarınızı environment variable olarak ayarlayın")
    print("   - OPENAI_API_KEY=your_key python examples/image_generation_example.py")
    print("   - REPLICATE_API_TOKEN=your_token python examples/image_generation_example.py")
    print("   - Oluşturulan resimlere URL'ler üzerinden erişebilirsiniz")
    print("   - Farklı model ve parametrelerle deneyim yapın")


if __name__ == "__main__":
    asyncio.run(main())