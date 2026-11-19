#!/usr/bin/env bash
set -euo pipefail
VER=${1:-1.0.0}
ARCH=${2:-x86_64}
if [ "$ARCH" = "x86_64" ]; then DEBARCH=amd64; else DEBARCH=arm64; fi
PKG=organizador-arquivos
ROOT="debbuild/${PKG}_${VER}_${DEBARCH}"
rm -rf "$ROOT"
mkdir -p "$ROOT/DEBIAN" "$ROOT/usr/bin" "$ROOT/usr/share/applications" "$ROOT/usr/share/icons/hicolor/256x256/apps"
install -m 755 dist/OrganizadorArquivos "$ROOT/usr/bin/OrganizadorArquivos"
  ln -sf OrganizadorArquivos "$ROOT/usr/bin/organizador-arquivos"
cp resources/organizador.desktop "$ROOT/usr/share/applications/organizador-arquivos.desktop"
cp resources/icon.png "$ROOT/usr/share/icons/hicolor/256x256/apps/organizador-arquivos.png"
cat > "$ROOT/DEBIAN/control" <<EOF
Package: $PKG
Version: $VER
Section: utils
Priority: optional
Architecture: $DEBARCH
Maintainer: FernandoGabrielSilva
Description: Organizador de Arquivos
 Organiza arquivos por tipo em pastas.
EOF
dpkg-deb --build "$ROOT" "OrganizadorArquivos_${VER}_${DEBARCH}.deb"
