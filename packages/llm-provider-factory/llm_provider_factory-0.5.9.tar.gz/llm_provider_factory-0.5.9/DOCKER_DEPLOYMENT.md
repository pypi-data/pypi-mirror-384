# 🐳 Docker Deployment Guide

This guide covers deploying LLM Provider Factory v0.4.1 with Docker, including both cloud and local LLM support.

## 🚀 Quick Start

### 1. Clone and Build
```bash
git clone https://github.com/sadikhanecioglu/llmfactory.py.git
cd llmfactory.py
```

### 2. Environment Setup
Create `.env` file:
```bash
# Cloud LLM API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GOOGLE_API_KEY=your_google_key_here
GOOGLE_CLOUD_PROJECT=your_gcp_project_id

# Local LLM Configuration
OLLAMA_BASE_URL=http://ollama:11434
```

### 3. Deploy with Docker Compose
```bash
# Start all services (LLM Factory + Ollama + Web UI)
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f llm-provider-factory
```

## 🔧 Configuration Options

### Docker Build Only
```bash
# Build the image
docker build -t llm-provider-factory:0.4.1 .

# Run container
docker run -d \
  --name llm_factory \
  -e OPENAI_API_KEY=your_key \
  -e ANTHROPIC_API_KEY=your_key \
  llm-provider-factory:0.4.1
```

### Custom Configuration
```bash
# Run with custom config
docker run -d \
  --name llm_factory \
  -v $(pwd)/config:/app/config \
  -e PYTHONPATH=/app \
  llm-provider-factory:0.4.1 \
  python your_custom_script.py
```

## 🌐 Service Endpoints

| Service | Port | URL | Description |
|---------|------|-----|-------------|
| LLM Provider Factory | - | Internal | Main service |
| Ollama API | 11434 | http://localhost:11434 | Local LLM API |
| Ollama Web UI | 3000 | http://localhost:3000 | Web interface |

## 🧪 Testing Deployment

### 1. Test Cloud Providers
```bash
docker exec -it llm_provider_factory python -c "
from llm_provider import LLMProviderFactory
from llm_provider.utils.config import OpenAIConfig
import asyncio

async def test():
    config = OpenAIConfig(api_key='your_key', model='gpt-3.5-turbo')
    factory = LLMProviderFactory()
    provider = factory.create_provider('openai', config)
    print('✅ OpenAI provider ready')

asyncio.run(test())
"
```

### 2. Test Local LLM (Ollama)
```bash
docker exec -it llm_provider_factory python -c "
from llm_provider import LLMProviderFactory
from llm_provider.utils.config import OllamaConfig
import asyncio

async def test():
    config = OllamaConfig(
        base_url='http://ollama:11434',
        model='llama3.1:latest'
    )
    factory = LLMProviderFactory()
    provider = factory.create_provider('ollama', config)
    print('✅ Ollama provider ready')

asyncio.run(test())
"
```

### 3. List Available Models
```bash
# Ollama models
curl http://localhost:11434/api/tags

# Or via docker
docker exec -it ollama ollama list
```

## 🔄 Container Management

### Start/Stop Services
```bash
# Start all
docker-compose up -d

# Stop all
docker-compose down

# Restart specific service
docker-compose restart llm-provider-factory

# Scale services
docker-compose up -d --scale llm-provider-factory=3
```

### Logs and Monitoring
```bash
# View logs
docker-compose logs -f [service_name]

# Monitor resources
docker stats

# Health check
docker-compose exec llm-provider-factory python -c "
from llm_provider import LLMProviderFactory
factory = LLMProviderFactory()
print(f'✅ {len(factory._providers)} providers available')
"
```

## 📦 Data Persistence

### Volumes
- `ollama_data`: Stores downloaded Ollama models
- `ollama_webui_data`: Stores web UI settings

### Backup Models
```bash
# Backup Ollama models
docker run --rm -v ollama_data:/data -v $(pwd):/backup ubuntu \
  tar czf /backup/ollama_models_backup.tar.gz /data

# Restore models
docker run --rm -v ollama_data:/data -v $(pwd):/backup ubuntu \
  tar xzf /backup/ollama_models_backup.tar.gz -C /
```

## ⚡ Performance Optimization

### Resource Limits
```yaml
# In docker-compose.yml
services:
  llm-provider-factory:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Ollama Performance
```yaml
ollama:
  environment:
    - OLLAMA_NUM_PARALLEL=2
    - OLLAMA_MAX_LOADED_MODELS=3
  deploy:
    resources:
      limits:
        memory: 8G
      reservations:
        memory: 4G
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Dependency Conflicts
```bash
# Check installed packages
docker exec -it llm_provider_factory pip list | grep pydantic
docker exec -it llm_provider_factory pip list | grep anthropic

# Should show:
# pydantic >= 2.0.0
# anthropic >= 0.39.0
```

#### 2. Ollama Connection
```bash
# Check Ollama health
curl http://localhost:11434/api/tags

# Check from container
docker exec -it llm_provider_factory curl http://ollama:11434/api/tags
```

#### 3. Memory Issues
```bash
# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"

# Clear unused data
docker system prune -a
```

### Debug Mode
```bash
# Run with debug logging
docker-compose up --build
docker-compose exec llm-provider-factory python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from llm_provider import LLMProviderFactory
"
```

## 🔐 Security

### Production Deployment
```yaml
# Use secrets for API keys
secrets:
  openai_key:
    file: ./secrets/openai_key.txt
  anthropic_key:
    file: ./secrets/anthropic_key.txt

services:
  llm-provider-factory:
    secrets:
      - openai_key
      - anthropic_key
    environment:
      - OPENAI_API_KEY_FILE=/run/secrets/openai_key
      - ANTHROPIC_API_KEY_FILE=/run/secrets/anthropic_key
```

### Network Security
```yaml
networks:
  llm_network:
    driver: bridge
    internal: true  # Isolate from external network
```

## 📊 Monitoring

### Health Checks
```bash
# Built-in health check
docker inspect --format='{{.State.Health.Status}}' llm_provider_factory

# Custom monitoring
docker exec -it llm_provider_factory python -c "
from llm_provider import LLMProviderFactory
import sys
try:
    factory = LLMProviderFactory()
    assert len(factory._providers) == 5
    print('✅ Health check passed')
    sys.exit(0)
except Exception as e:
    print(f'❌ Health check failed: {e}')
    sys.exit(1)
"
```

## 🚀 Production Tips

1. **Use specific versions** in production:
   ```yaml
   image: llm-provider-factory:0.4.1
   ```

2. **Resource monitoring**:
   ```bash
   docker-compose exec llm-provider-factory python -c "
   import psutil
   print(f'CPU: {psutil.cpu_percent()}%')
   print(f'Memory: {psutil.virtual_memory().percent}%')
   "
   ```

3. **Log aggregation**:
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "100m"
       max-file: "3"
   ```

4. **Auto-restart**:
   ```yaml
   restart: unless-stopped
   ```

This deployment is optimized for v0.4.1 with fixed pydantic dependencies! 🎉