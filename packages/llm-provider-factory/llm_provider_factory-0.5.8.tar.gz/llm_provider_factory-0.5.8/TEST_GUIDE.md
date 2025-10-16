# 🧪 Test Dosyaları

Bu klasörde image generation özelliklerini test etmek için çeşitli test dosyaları bulunmaktadır:

## 🚀 Hızlı Testler

### `quick_image_test.py`
```bash
python quick_image_test.py
```
- **Amaç**: Temel functionality kontrolü
- **API Key Gerekli**: Hayır (temel test), Evet (API testi için)
- **Süre**: ~10 saniye
- **Test Eder**: Import'lar, factory creation, provider methods

### `demo_image_generation.py` 
```bash
export OPENAI_API_KEY="sk-your-key"
export REPLICATE_API_TOKEN="r8_your-token"
python demo_image_generation.py
```
- **Amaç**: İnteraktif demo ve test
- **API Key Gerekli**: Evet
- **Süre**: Kullanıcı girişine bağlı
- **Test Eder**: OpenAI DALL-E, Replicate SDXL, Combined LLM+Image

## 🔬 Kapsamlı Testler

### `test_image_providers_real.py`
```bash
export OPENAI_API_KEY="sk-your-key"
export REPLICATE_API_TOKEN="r8_your-token"
python test_image_providers_real.py
```
- **Amaç**: Gerçek API'larla otomatik test
- **API Key Gerekli**: Evet
- **Süre**: ~2-5 dakika
- **Test Eder**: 
  - OpenAI DALL-E 2 & 3
  - Replicate Stable Diffusion XL
  - Combined LLM + Image workflow
  - Performance metrics
  - Error handling

## 📊 Test Senaryoları

### OpenAI DALL-E Testleri
- ✅ DALL-E 3 ile HD kalite resim
- ✅ DALL-E 2 ile standart resim  
- ✅ Farklı boyutlar (512x512, 1024x1024, 1024x1792)
- ✅ Kalite seçenekleri (standard, hd)
- ✅ Stil kontrolleri (vivid, natural)

### Replicate Testleri
- ✅ Stable Diffusion XL
- ✅ Custom model support
- ✅ Inference steps kontrolü
- ✅ Guidance scale ayarları
- ✅ Reference image desteği

### Combined Workflow Testleri
- ✅ LLM ile prompt generation
- ✅ Generated prompt ile image creation
- ✅ End-to-end workflow timing
- ✅ Error propagation

## 🛠️ Test Kurulumu

### 1. Environment Variables
```bash
# OpenAI için
export OPENAI_API_KEY="sk-proj-your-openai-key"

# Replicate için  
export REPLICATE_API_TOKEN="r8_your-replicate-token"
```

### 2. Dependencies
```bash
# Temel dependencies zaten yüklü
pip install -e .

# Replicate için (opsiyonel, fallback HTTP client mevcut)
pip install replicate
```

### 3. Test Komutları

#### Hızlı Kontrol
```bash
python quick_image_test.py
```

#### İnteraktif Demo
```bash
python demo_image_generation.py
```

#### Tam Test Suite
```bash
python test_image_providers_real.py
```

## 📈 Beklenen Sonuçlar

### Başarılı Test Çıktısı
```
🎨 Image Provider Real API Tester
==================================================
✅ OPENAI_API_KEY found
✅ REPLICATE_API_TOKEN found

🎨 Testing OpenAI DALL-E
------------------------------
✅ Generation successful!
   Duration: 12.45 seconds
   Model: dall-e-3
   Image URL: https://oaidalleapiprodscus.blob.core.windows.net/...

📊 Test Summary
==================================================
✅ Successful: 3
❌ Failed: 0
```

### Performance Benchmarks
- **OpenAI DALL-E 3**: ~10-15 saniye
- **OpenAI DALL-E 2**: ~8-12 saniye  
- **Replicate SDXL**: ~15-30 saniye
- **LLM + Image Workflow**: ~20-40 saniye

## 🚨 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Solution: Install in development mode
pip install -e .
```

#### API Key Errors
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $REPLICATE_API_TOKEN

# Re-export if needed
export OPENAI_API_KEY="your-key"
```

#### Rate Limits
- OpenAI: 5 requests/minute (free tier)
- Replicate: Varies by model
- **Solution**: Add delays between tests

#### Network Timeouts
```python
# Increase timeout in config
config = OpenAIImageConfig(
    api_key="your-key",
    timeout=120  # 2 minutes
)
```

## 💡 Tips

1. **Start Small**: `quick_image_test.py` ile başlayın
2. **Interactive Testing**: `demo_image_generation.py` kullanın
3. **Full Testing**: `test_image_providers_real.py` ile comprehensive test
4. **Cost Control**: API çağrıları ücretli - test sayısını kontrol edin
5. **URL Saving**: Generated image URL'leri kaydedin, temporary olabilir

## 🔗 Links

- [OpenAI DALL-E API](https://platform.openai.com/docs/guides/images)
- [Replicate Image Models](https://replicate.com/collections/text-to-image)
- [Stable Diffusion XL](https://replicate.com/stability-ai/sdxl)