#!/usr/bin/env python3
"""
Real API Test for Image Providers

Bu test gerçek API'lar ile image generation provider'ları test eder.
Environment variable'lar gereklidir:
- OPENAI_API_KEY: OpenAI DALL-E için
- REPLICATE_API_TOKEN: Replicate için

Kullanım:
    export OPENAI_API_KEY="sk-your-openai-key"
    export REPLICATE_API_TOKEN="r8_your-replicate-token"
    python test_image_providers_real.py
"""

import asyncio
import os
import sys
import time
from datetime import datetime
from typing import Optional

# Local import
sys.path.insert(0, "src")

try:
    from llm_provider import ImageProviderFactory, LLMProviderFactory
    print("✅ LLM Provider imports successful")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're in the project root directory")
    sys.exit(1)


class ImageProviderTester:
    """Real API test class for image providers"""
    
    def __init__(self):
        self.factory = ImageProviderFactory()
        self.results = {}
        self.start_time = datetime.now()
        
        # API Keys
        self.openai_key = os.getenv("OPENAI_API_KEY")
        self.replicate_token = os.getenv("REPLICATE_API_TOKEN")
        
        print("🧪 Image Provider Real API Tester")
        print("=" * 50)
        print(f"🕐 Test started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Check API keys
        if self.openai_key:
            print("✅ OPENAI_API_KEY found")
        else:
            print("⚠️  OPENAI_API_KEY not found - OpenAI tests will be skipped")
            
        if self.replicate_token:
            print("✅ REPLICATE_API_TOKEN found")
        else:
            print("⚠️  REPLICATE_API_TOKEN not found - Replicate tests will be skipped")
        print()
    
    async def test_openai_dalle(self):
        """Test OpenAI DALL-E image generation"""
        if not self.openai_key:
            print("⏭️  Skipping OpenAI test - no API key")
            return
        
        print("🎨 Testing OpenAI DALL-E")
        print("-" * 30)
        
        try:
            # Create provider
            provider = self.factory.create_openai_image(
                api_key=self.openai_key,
                model="dall-e-3",
                size="1024x1024",
                quality="standard"
            )
            
            # Test simple generation
            print("📝 Generating: 'A cute robot holding a paintbrush'")
            start_time = time.time()
            
            response = await provider.generate_image(
                prompt="A cute robot holding a paintbrush, digital art style",
                size="1024x1024",
                quality="standard"
            )
            
            duration = time.time() - start_time
            
            print(f"✅ Generation successful!")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Model: {response.model}")
            print(f"   Size: {response.size}")
            print(f"   URLs generated: {len(response.urls)}")
            print(f"   Image URL: {response.urls[0][:80]}...")
            print(f"   Created at: {response.created_at}")
            
            self.results["openai_dalle"] = {
                "status": "success",
                "duration": duration,
                "model": response.model,
                "url": response.urls[0]
            }
            
            # Test DALL-E 2 as well
            print()
            print("📝 Testing DALL-E 2: 'A sunset over mountains'")
            start_time = time.time()
            
            provider2 = self.factory.create_openai_image(
                api_key=self.openai_key,
                model="dall-e-2",
                size="512x512"
            )
            
            response2 = await provider2.generate_image(
                prompt="A beautiful sunset over snow-capped mountains",
                size="512x512"
            )
            
            duration2 = time.time() - start_time
            
            print(f"✅ DALL-E 2 generation successful!")
            print(f"   Duration: {duration2:.2f} seconds")
            print(f"   Model: {response2.model}")
            print(f"   Image URL: {response2.urls[0][:80]}...")
            
            self.results["openai_dalle2"] = {
                "status": "success",
                "duration": duration2,
                "model": response2.model,
                "url": response2.urls[0]
            }
            
        except Exception as e:
            print(f"❌ OpenAI test failed: {e}")
            self.results["openai_dalle"] = {
                "status": "failed",
                "error": str(e)
            }
        
        print()
    
    async def test_replicate_sdxl(self):
        """Test Replicate Stable Diffusion XL"""
        if not self.replicate_token:
            print("⏭️  Skipping Replicate test - no API token")
            return
        
        print("🔄 Testing Replicate Stable Diffusion XL")
        print("-" * 40)
        
        try:
            # Create provider
            provider = self.factory.create_replicate_image(
                api_token=self.replicate_token,
                model="stability-ai/sdxl:39ed52f2a78e934b3ba6e2a89f5b1c712de7dfea535525255b1aa35c5565e08b",
                width=1024,
                height=1024
            )
            
            # Test generation
            print("📝 Generating: 'A cyberpunk cityscape at night'")
            start_time = time.time()
            
            response = await provider.generate_image(
                prompt="A cyberpunk cityscape at night with neon lights and flying cars, highly detailed, 4k",
                width=1024,
                height=1024,
                num_inference_steps=30,
                guidance_scale=7.5
            )
            
            duration = time.time() - start_time
            
            print(f"✅ Generation successful!")
            print(f"   Duration: {duration:.2f} seconds")
            print(f"   Model: {response.model}")
            print(f"   Size: {response.size}")
            print(f"   URLs generated: {len(response.urls)}")
            print(f"   Image URL: {response.urls[0][:80]}...")
            
            self.results["replicate_sdxl"] = {
                "status": "success",
                "duration": duration,
                "model": response.model,
                "url": response.urls[0]
            }
            
        except Exception as e:
            print(f"❌ Replicate test failed: {e}")
            self.results["replicate_sdxl"] = {
                "status": "failed",
                "error": str(e)
            }
        
        print()
    
    async def test_combined_llm_image(self):
        """Test combined LLM + Image generation"""
        if not self.openai_key:
            print("⏭️  Skipping combined test - no OpenAI API key")
            return
        
        print("🤖 Testing Combined LLM + Image Generation")
        print("-" * 45)
        
        try:
            # First, use LLM to generate image prompt
            llm_factory = LLMProviderFactory()
            llm_provider = llm_factory.create_openai(
                api_key=self.openai_key,
                model="gpt-3.5-turbo"
            )
            
            print("📝 Step 1: Generating image prompt with LLM...")
            llm_start = time.time()
            
            llm_response = await llm_provider.generate(
                "Create a detailed, artistic prompt for an AI image generator. "
                "Describe a magical forest scene with fantastical creatures. "
                "Keep it under 100 words and make it very descriptive and artistic."
            )
            
            llm_duration = time.time() - llm_start
            generated_prompt = llm_response.content.strip()
            
            print(f"✅ LLM prompt generated in {llm_duration:.2f}s")
            print(f"   Generated prompt: {generated_prompt}")
            print()
            
            # Now use that prompt for image generation
            print("📝 Step 2: Generating image with LLM-created prompt...")
            image_start = time.time()
            
            image_provider = self.factory.create_openai_image(
                api_key=self.openai_key,
                model="dall-e-3",
                size="1024x1024"
            )
            
            image_response = await image_provider.generate_image(
                prompt=generated_prompt,
                size="1024x1024",
                quality="standard"
            )
            
            image_duration = time.time() - image_start
            
            print(f"✅ Image generated in {image_duration:.2f}s")
            print(f"   Total workflow time: {llm_duration + image_duration:.2f}s")
            print(f"   Image URL: {image_response.urls[0][:80]}...")
            
            self.results["combined_workflow"] = {
                "status": "success",
                "llm_duration": llm_duration,
                "image_duration": image_duration,
                "total_duration": llm_duration + image_duration,
                "generated_prompt": generated_prompt,
                "image_url": image_response.urls[0]
            }
            
        except Exception as e:
            print(f"❌ Combined test failed: {e}")
            self.results["combined_workflow"] = {
                "status": "failed",
                "error": str(e)
            }
        
        print()
    
    async def run_all_tests(self):
        """Run all image provider tests"""
        print("🚀 Starting Real API Tests")
        print("=" * 50)
        print()
        
        # Test individual providers
        await self.test_openai_dalle()
        await self.test_replicate_sdxl()
        await self.test_combined_llm_image()
        
        # Print final summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        end_time = datetime.now()
        total_duration = (end_time - self.start_time).total_seconds()
        
        print("📊 Test Summary")
        print("=" * 50)
        print(f"🕐 Total test time: {total_duration:.2f} seconds")
        print(f"🧪 Tests run: {len(self.results)}")
        
        success_count = sum(1 for r in self.results.values() if r.get("status") == "success")
        print(f"✅ Successful: {success_count}")
        print(f"❌ Failed: {len(self.results) - success_count}")
        print()
        
        # Detailed results
        for test_name, result in self.results.items():
            status_emoji = "✅" if result.get("status") == "success" else "❌"
            print(f"{status_emoji} {test_name}:")
            
            if result.get("status") == "success":
                if "duration" in result:
                    print(f"   Duration: {result['duration']:.2f}s")
                if "model" in result:
                    print(f"   Model: {result['model']}")
                if "url" in result:
                    print(f"   Image: {result['url'][:60]}...")
            else:
                print(f"   Error: {result.get('error', 'Unknown error')}")
            print()
        
        print("🎉 Real API testing completed!")
        
        if success_count > 0:
            print()
            print("💡 Generated images can be accessed via the URLs above")
            print("   Copy the URLs to your browser to view the images")


async def main():
    """Main test function"""
    # Check if we're in the right directory
    if not os.path.exists("src/llm_provider"):
        print("❌ Error: Not in project root directory")
        print("   Please run from the project root where src/llm_provider exists")
        sys.exit(1)
    
    # Check for API keys
    openai_key = os.getenv("OPENAI_API_KEY")
    replicate_token = os.getenv("REPLICATE_API_TOKEN")
    
    if not openai_key and not replicate_token:
        print("❌ Error: No API keys found!")
        print()
        print("Please set environment variables:")
        print("   export OPENAI_API_KEY='sk-your-openai-key'")
        print("   export REPLICATE_API_TOKEN='r8_your-replicate-token'")
        print()
        print("Then run: python test_image_providers_real.py")
        sys.exit(1)
    
    # Run tests
    tester = ImageProviderTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        sys.exit(1)