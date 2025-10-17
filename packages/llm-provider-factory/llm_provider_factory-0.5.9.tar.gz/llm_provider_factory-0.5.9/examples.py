"""
Example usage of LLM Provider Factory.

This script demonstrates various ways to use the LLM Provider Factory
with different providers and configurations.
"""

import asyncio
import os
from llm_provider import (
    LLMProviderFactory,
    OpenAI, Anthropic, Gemini, VertexAI,
    OpenAIConfig, AnthropicConfig, GeminiConfig, VertexAIConfig,
    Message, MessageRole
)


async def basic_usage_example():
    """Basic usage example with OpenAI."""
    print("=== Basic Usage Example ===")
    
    # Method 1: Using the factory with a provider instance
    factory = LLMProviderFactory(OpenAI())
    
    try:
        response = await factory.generate("Hello, world! Tell me a fun fact.")
        print(f"Response: {response.content}")
        print(f"Provider: {response.provider}")
        print(f"Model: {response.model}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def configuration_example():
    """Example using custom configuration."""
    print("=== Configuration Example ===")
    
    # Create custom configuration
    config = OpenAIConfig(
        api_key=os.getenv("OPENAI_API_KEY", "your-api-key-here"),
        model="gpt-3.5-turbo",
        max_tokens=100,
        temperature=0.8
    )
    
    factory = LLMProviderFactory.create_openai(config)
    
    try:
        response = await factory.generate("Write a haiku about programming")
        print(f"Response: {response.content}")
        if response.usage:
            print(f"Tokens used: {response.usage}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def multiple_providers_example():
    """Example using multiple providers."""
    print("=== Multiple Providers Example ===")
    
    factory = LLMProviderFactory()
    prompt = "Explain what makes a good API design in one sentence."
    
    providers = ["openai", "anthropic", "gemini", "vertexai"]
    
    for provider_name in providers:
        try:
            print(f"\n--- {provider_name.upper()} ---")
            response = await factory.generate(prompt, provider=provider_name)
            print(f"Response: {response.content}")
        except Exception as e:
            print(f"Error with {provider_name}: {e}")
    
    print()


async def conversation_example():
    """Example with conversation history."""
    print("=== Conversation Example ===")
    
    factory = LLMProviderFactory.create_openai()
    
    # Build conversation history
    history = [
        Message(role=MessageRole.SYSTEM, content="You are a helpful programming assistant."),
        Message(role=MessageRole.USER, content="I'm learning Python. What are variables?"),
        Message(role=MessageRole.ASSISTANT, content="Variables in Python are containers that store data values. You can think of them as labeled boxes where you can put different types of information like numbers, text, or more complex data."),
        Message(role=MessageRole.USER, content="Can you give me an example?")
    ]
    
    try:
        response = await factory.generate(
            "Now explain functions and how they relate to variables",
            history=history,
            max_tokens=200
        )
        print(f"Response: {response.content}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def streaming_example():
    """Example with streaming responses."""
    print("=== Streaming Example ===")
    
    factory = LLMProviderFactory.create_openai()
    
    try:
        print("Streaming response:")
        content = ""
        async for chunk in factory.stream_generate(
            "Write a very short story about a robot learning to paint",
            max_tokens=150
        ):
            if chunk.content:
                print(chunk.content, end="", flush=True)
                content += chunk.content
            
            if chunk.is_final:
                print(f"\n\nStream finished. Reason: {chunk.finish_reason}")
                print(f"Total content length: {len(content)} characters")
                break
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def provider_info_example():
    """Example showing provider information."""
    print("=== Provider Information Example ===")
    
    factory = LLMProviderFactory()
    
    # Get all available providers
    print("Available providers:")
    for provider_name in factory.get_available_providers():
        print(f"- {provider_name}")
    
    print("\nDetailed provider information:")
    try:
        # Get information about all providers
        all_info = factory.get_provider_info()
        for info in all_info:
            print(f"\n{info.display_name}:")
            print(f"  Description: {info.description}")
            print(f"  Available: {info.is_available}")
            print(f"  Models: {', '.join(info.supported_models[:3])}...")  # Show first 3 models
            print(f"  Capabilities: {', '.join(info.capabilities)}")
    except Exception as e:
        print(f"Error getting provider info: {e}")
    
    print()


async def error_handling_example():
    """Example demonstrating error handling."""
    print("=== Error Handling Example ===")
    
    from llm_provider import (
        AuthenticationError,
        RateLimitError,
        ModelNotAvailableError,
        GenerationError,
        InvalidConfigurationError
    )
    
    # Example with invalid configuration
    try:
        config = OpenAIConfig(api_key="invalid-key")
        factory = LLMProviderFactory.create_openai(config)
        await factory.generate("This will fail")
    except AuthenticationError as e:
        print(f"Authentication error: {e}")
    except InvalidConfigurationError as e:
        print(f"Configuration error: {e}")
    except Exception as e:
        print(f"General error: {e}")
    
    print()


async def parameter_customization_example():
    """Example with custom parameters."""
    print("=== Parameter Customization Example ===")
    
    factory = LLMProviderFactory.create_openai()
    
    try:
        # Generate with custom parameters
        response = await factory.generate(
            "Explain quantum computing",
            max_tokens=50,          # Limit response length
            temperature=0.1,        # Low temperature for focused response
            top_p=0.9,             # Nucleus sampling
            stop_sequences=[".", "!"]  # Stop at first sentence
        )
        print(f"Focused response: {response.content}")
        print(f"Finish reason: {response.finish_reason}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()


async def main():
    """Run all examples."""
    print("🤖 LLM Provider Factory Examples\n")
    print("Note: Make sure you have API keys set in your environment:")
    print("- OPENAI_API_KEY")
    print("- ANTHROPIC_API_KEY") 
    print("- GOOGLE_API_KEY")
    print("=" * 50)
    
    await basic_usage_example()
    await configuration_example()
    await multiple_providers_example()
    await conversation_example()
    await streaming_example()
    await provider_info_example()
    await error_handling_example()
    await parameter_customization_example()
    
    print("✅ All examples completed!")


if __name__ == "__main__":
    asyncio.run(main())