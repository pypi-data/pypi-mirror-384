#!/bin/bash

# Version güncelleme ve yayınlama scripti

if [ $# -eq 0 ]; then
    echo "Kullanım: ./release.sh <version>"
    echo "Örnek: ./release.sh 0.1.1"
    exit 1
fi

VERSION=$1

echo "🔄 Version $VERSION için yayın hazırlanıyor..."

# 1. pyproject.toml'daki version'ı güncelle
sed -i '' "s/version = \".*\"/version = \"$VERSION\"/" pyproject.toml

# 2. Eski build dosyalarını temizle
rm -rf dist/ build/ *.egg-info/

# 3. Yeni build oluştur
python -m build

# 4. Build'i kontrol et
twine check dist/*

echo "✅ Build hazır!"
echo "🧪 Test PyPI için: ./upload_test.sh"
echo "🚀 Gerçek PyPI için: ./upload_pypi.sh"

# 5. Git tag oluştur (isteğe bağlı)
read -p "Git tag oluşturulsun mu? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git tag -a "v$VERSION" -m "Release version $VERSION"
    echo "📝 Git tag v$VERSION oluşturuldu"
    echo "💾 Push etmeyi unutmayın: git push origin v$VERSION"
fi