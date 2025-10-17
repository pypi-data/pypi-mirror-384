# 🦙 Ollama Setup Rehberi

## 📥 1. Ollama Kurulumu

### macOS:
```bash
# Homebrew ile
brew install ollama

# Veya direkt indirin
curl -fsSL https://ollama.ai/install.sh | sh
```

### Linux:
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

### Windows:
- [ollama.ai](https://ollama.ai) adresinden indirin

## 🚀 2. Ollama Server Başlatma

```bash
# Server'ı başlat (background'da çalışır)
ollama serve

# Veya macOS'ta service olarak
brew services start ollama
```

## 📦 3. Model İndirme

```bash
# Önerilen modeller
ollama pull llama3.1:latest     # En yeni, güçlü
ollama pull llama2              # Hızlı, orta boyut
ollama pull codellama           # Kod için özel
ollama pull mistral             # Hafif ve hızlı

# Modelleri listele
ollama list
```

## 🧪 4. Test Etme

```bash
# Terminal'de test
ollama run llama3.1:latest "Python nedir?"

# API test
curl http://localhost:11434/api/tags
```

## 🔧 5. LLM Provider Factory ile Kullanım

```python
from llm_provider import LLMProviderFactory
from llm_provider.utils.config import OllamaConfig

# Config
config = OllamaConfig(
    base_url="http://localhost:11434",
    model="llama3.1:latest"
)

# Provider
factory = LLMProviderFactory()
provider = factory.create_provider("ollama", config)
```

## 📊 6. Desteklenen Modeller

| Model | Boyut | Kullanım | Önerilen |
|-------|-------|----------|----------|
| llama3.1:latest | ~4.7GB | Genel amaçlı | ✅ En iyi |
| llama2 | ~3.8GB | Hızlı cevaplar | ✅ Başlangıç |
| codellama | ~3.8GB | Kod üretimi | 💻 Kod için |
| mistral | ~4.1GB | Matematik/Logic | 🧮 Analitik |
| neural-chat | ~4.1GB | Konversasyon | 💬 Chat için |

## ⚡ 7. Performance İpuçları

### Hız için:
```python
config = OllamaConfig(
    model="llama2",           # Daha küçük model
    max_tokens=100,           # Kısa cevaplar
    temperature=0.3           # Düşük creativity
)
```

### Kalite için:
```python
config = OllamaConfig(
    model="llama3.1:latest",  # En iyi model
    max_tokens=500,           # Uzun cevaplar
    temperature=0.8,          # Yüksek creativity
    top_p=0.9
)
```

## 🚨 8. Sorun Giderme

### Server çalışmıyor:
```bash
# Process kontrol
ps aux | grep ollama

# Port kontrol  
lsof -i :11434

# Yeniden başlat
killall ollama
ollama serve
```

### Model yok hatası:
```bash
# Mevcut modeller
ollama list

# Model indir
ollama pull llama3.1:latest
```

### Bağlantı hatası:
```python
# URL kontrol
config = OllamaConfig(
    base_url="http://localhost:11434",  # Doğru port
    model="llama3.1:latest"
)
```

## 🎯 9. Production İpuçları

### Docker ile:
```dockerfile
FROM ollama/ollama
RUN ollama pull llama3.1:latest
EXPOSE 11434
```

### Monitoring:
```bash
# Resource kullanım
htop

# Model boyutları
du -sh ~/.ollama/models/*
```

### API Limits:
```python
config = OllamaConfig(
    max_tokens=1000,      # Token limiti
    timeout=30,           # Timeout (saniye)
    temperature=0.7       # Deterministik için düşük
)
```

## 📚 10. Örnekler

Detaylı örnekler için:
- `ollama_quickstart.py` - Hızlı başlangıç
- `ollama_examples.py` - Kapsamlı örnekler
- `test_ollama_only.py` - Test dosyası

## 🆘 Yardım

- [Ollama Documentation](https://github.com/ollama/ollama)
- [Model Library](https://ollama.ai/library)
- [GitHub Issues](https://github.com/sadikhanecioglu/llmfactory.py/issues)