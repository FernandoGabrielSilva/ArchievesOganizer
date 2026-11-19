#!/usr/bin/env bash
set -e
APP=OrganizadorArquivos
BASE="$(cd "$(dirname "$0")" && pwd)"
APPDIR="$BASE/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$BASE/dist/OrganizadorArquivos" "$APPDIR/usr/bin/OrganizadorArquivos"
chmod +x "$APPDIR/usr/bin/OrganizadorArquivos"

cp "$BASE/resources/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP.png"
cp "$BASE/resources/icon.png" "$APPDIR/$APP.png"

cp "$BASE/resources/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

cp "$BASE/resources/organizador.desktop" "$APPDIR/$APP.desktop"
cp "$BASE/resources/organizador.desktop" "$APPDIR/usr/share/applications/"

echo "AppDir pronto."
