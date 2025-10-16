#!/bin/bash

# Test PyPI'ye yükleme scripti
echo "🧪 Test PyPI'ye yükleniyor..."

# Test PyPI'ye yükle
twine upload --repository testpypi dist/*

echo "✅ Test PyPI'ye yükleme tamamlandı!"
echo "📦 Test etmek için: pip install --index-url https://test.pypi.org/simple/ llm-provider-factory"