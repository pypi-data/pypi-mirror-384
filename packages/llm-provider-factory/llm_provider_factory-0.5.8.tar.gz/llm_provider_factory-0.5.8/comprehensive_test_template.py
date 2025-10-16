#!/usr/bin/env python3
"""
Comprehensive LLM Provider Test Suite - Template
Tüm provider'ları (OpenAI, Anthropic, Gemini, VertexAI, Ollama) test eder

🔑 Bu dosyayı kopyalayın ve API key'lerinizi girin
📁 .gitignore'da - güvenle kullanabilirsiniz
"""

# ==========================================
# 🔑 API KEYS - BURAYA GİRİN
# ==========================================

# OpenAI
OPENAI_API_KEY = "sk-proj-..."  # OpenAI API key'inizi buraya girin

# Anthropic
ANTHROPIC_API_KEY = "sk-ant-..."  # Anthropic API key'inizi buraya girin

# Google Gemini
GOOGLE_API_KEY = "AIza..."  # Google API key'inizi buraya girin

# Google Cloud VertexAI
GOOGLE_CLOUD_PROJECT = "your-project-id"  # Google Cloud project ID'nizi girin
GOOGLE_APPLICATION_CREDENTIALS = "/path/to/service-account.json"  # JSON dosya yolu

# Ollama (Local LLM Server)
OLLAMA_BASE_URL = "http://localhost:11434"  # Ollama server URL'i
OLLAMA_MODEL = "llama3.1:latest"  # Varsayılan Ollama model

# ==========================================
# 🎯 TEST PROMPT
# ==========================================
TEST_PROMPT = "Merhaba! Sen kimsin ve hangi konularda yardım edebilirsin? Kısa bir cevap ver."

# ==========================================
# 📋 TEST KONFİGÜRASYONU
# ==========================================

# Test edilecek modeller (istediğinizi kaldırabilirsiniz)
TEST_MODELS = {
    'openai': ['gpt-3.5-turbo', 'gpt-4o-mini'],
    'anthropic': ['claude-3-haiku-20240307', 'claude-3-sonnet-20240229'],
    'gemini': ['gemini-1.5-flash', 'gemini-1.5-pro'],
    'vertexai': ['gemini-1.5-flash', 'mistral-large-2411'],
    'ollama': ['llama3.1:latest', 'llama2', 'codellama']
}

# Test türleri (True/False ile aktif/pasif yapabilirsiniz)
ENABLE_TESTS = {
    'basic_generation': True,
    'conversation': True,
    'streaming': True
}

# ==========================================
# 📝 KULLANIM TALİMATLARI
# ==========================================
"""
1. Bu dosyayı kopyalayın: cp comprehensive_test_template.py my_test.py
2. API key'lerinizi yukarıya girin
3. İstediğiniz test'leri aktif/pasif yapın
4. Çalıştırın: python my_test.py

🔒 Güvenlik:
- Bu template dosyası git'e yüklenebilir (key'ler yok)
- Kopyaladığınız dosya .gitignore'da olmalı
- Asla gerçek API key'leri git'e yüklemeyin!
"""

print("🚨 Bu bir template dosyasıdır!")
print("📋 Gerçek test için:")
print("1. Bu dosyayı kopyalayın")
print("2. API key'leri girin") 
print("3. Çalıştırın")
print()
print("Örnek: cp comprehensive_test_template.py my_test.py")