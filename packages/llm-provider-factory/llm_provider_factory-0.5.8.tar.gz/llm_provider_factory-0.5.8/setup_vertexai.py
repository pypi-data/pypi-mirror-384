#!/usr/bin/env python3
"""
VertexAI Environment Setup Script
Bu script VertexAI kullanımı için gerekli paketleri yükler
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} başarılı")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} başarısız: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_vertexai():
    """Setup VertexAI environment"""
    
    print("🚀 VertexAI Environment Setup Başlıyor...")
    
    # Install required packages
    packages = [
        "google-cloud-aiplatform",
        "google-auth",
        "google-auth-oauthlib",
        "google-cloud-core",
        "protobuf"
    ]
    
    for package in packages:
        if not run_command(f"pip install {package}", f"{package} paketi yükleniyor"):
            return False
    
    print("\n✅ Tüm paketler başarıyla yüklendi!")
    
    # Check installation
    print("\n🔍 Kurulum kontrolü...")
    
    try:
        import google.cloud.aiplatform
        import vertexai
        from vertexai.generative_models import GenerativeModel
        print("✅ VertexAI paketleri başarıyla import edildi")
    except ImportError as e:
        print(f"❌ Import hatası: {e}")
        return False
    
    # Environment setup instructions
    print("\n📋 Sonraki adımlar:")
    print("1. Google Cloud Console'dan service account oluşturun")
    print("2. Service account için JSON key dosyası indirin") 
    print("3. GOOGLE_APPLICATION_CREDENTIALS environment variable'ını ayarlayın:")
    print("   export GOOGLE_APPLICATION_CREDENTIALS='/path/to/your/credentials.json'")
    print("4. Vertex AI API'yi etkinleştirin: https://console.cloud.google.com/apis/library/aiplatform.googleapis.com")
    print("5. Test scriptini çalıştırın: python test_vertexai_mistral.py")
    
    return True

if __name__ == "__main__":
    success = setup_vertexai()
    if success:
        print("\n🎉 Setup tamamlandı!")
    else:
        print("\n❌ Setup başarısız oldu")
        sys.exit(1)