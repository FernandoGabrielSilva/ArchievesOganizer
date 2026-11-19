#!/usr/bin/env bash
set -euo pipefail
VER=${1:-1.0.0}
ARCH=${2:-x86_64}
DEST="organizador-arquivos-${VER}-1-${ARCH}.pkg.tar.zst"
TMP=archpkg
rm -rf "$TMP" "$DEST"
mkdir -p "$TMP/usr/bin" "$TMP/usr/share/applications" "$TMP/usr/share/icons/hicolor/256x256/apps"
install -m 755 OrganizadorArquivos "$TMP/usr/bin/organizador-arquivos"
install -m 644 organizador.desktop "$TMP/usr/share/applications/organizador-arquivos.desktop"
install -m 644 icon.png "$TMP/usr/share/icons/hicolor/256x256/apps/organizador-arquivos.png"
cat > "$TMP/.PKGINFO" <<EOF
pkgname = organizador-arquivos
pkgver = ${VER}-1
pkgdesc = Organizador de Arquivos
url = https://github.com/FernandoGabrielSilva/ArchievesOganizer
license = MIT
arch = ${ARCH}
EOF
tar --zstd -cf "$DEST" -C "$TMP" .
