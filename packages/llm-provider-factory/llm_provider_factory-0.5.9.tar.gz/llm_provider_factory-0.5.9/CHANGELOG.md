# Changelog

All notable changes to this project will be documented in this file.

## [0.4.1] - 2025-10-09

### Fixed
- **Docker Compatibility**: Fixed pydantic dependency conflict for Docker deployments
  - Updated `anthropic` dependency from `>=0.3.0` to `>=0.39.0` (pydantic v2 compatible)
  - Ensures compatibility with modern deployment environments
  - Resolves dependency conflicts in containerized environments

### Dependencies
- anthropic: `>=0.3.0` → `>=0.39.0` (pydantic v2 support)

### Docker Deployment
This version is specifically optimized for Docker and containerized deployments.

## [0.4.0] - 2025-10-08

### Added
- **Ollama Provider**: Complete local LLM support
  - Support for 16+ Ollama models (llama3.1, llama2, codellama, etc.)
  - Full streaming support with real-time chunks
  - Conversation and basic generation capabilities
  - HTTP API integration at localhost:11434

### Features
- Unified interface for both cloud and local LLMs
- Factory pattern for easy provider switching
- Comprehensive error handling
- Type safety with Pydantic v2

### Providers
- ✅ OpenAI (GPT-3.5, GPT-4, GPT-4o)
- ✅ Anthropic (Claude-3 models)
- ✅ Google Gemini
- ✅ VertexAI (Mistral models)
- ✅ Ollama (Local LLMs)

### Tested
- All 5 providers working ✅
- Streaming support ✅
- Local LLM integration ✅
- Comprehensive test suite ✅

## [0.3.3] - 2025-10-07

### Added
- VertexAI provider with Mistral support
- Complete async/await implementation
- Streaming capabilities

### Fixed
- Abstract method implementations
- Provider initialization issues

## [0.3.0] - 2025-10-06

### Added
- Initial release with OpenAI, Anthropic, and Gemini providers
- Factory pattern implementation
- Comprehensive configuration system