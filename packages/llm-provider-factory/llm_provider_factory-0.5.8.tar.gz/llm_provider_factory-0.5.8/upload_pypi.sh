#!/bin/bash

# PyPI'ye yükleme scripti
echo "🚀 PyPI'ye yükleniyor..."

# Gerçek PyPI'ye yükle
twine upload dist/*

echo "✅ PyPI'ye yükleme tamamlandı!"
echo "📦 Yüklemek için: pip install llm-provider-factory"