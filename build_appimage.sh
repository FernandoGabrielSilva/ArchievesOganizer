#!/usr/bin/env bash
set -e
APP=OrganizadorArquivos
BASE="$(cd "$(dirname "$0")" && pwd)"
cd "$BASE"

# O AppImage precisa do binário onefile gerado pelo PyInstaller.
if [ ! -x dist/$APP ]; then
    echo "Binário não encontrado. Gerando com PyInstaller..."
    python3 -m PyInstaller --noconfirm --windowed --onefile --name "$APP" main.py \
        --hidden-import organizer --collect-all qfluentwidgets --collect-all PySide6
fi

if [ ! -x "dist/$APP" ]; then
    echo "Falha: dist/$APP não foi gerado pelo PyInstaller." >&2
    exit 1
fi

APPDIR="$BASE/AppDir"
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin" "$APPDIR/usr/share/applications" "$APPDIR/usr/share/icons/hicolor/256x256/apps"

cp "$BASE/dist/$APP" "$APPDIR/usr/bin/$APP"
chmod +x "$APPDIR/usr/bin/$APP"

cp "$BASE/resources/icon.png" "$APPDIR/usr/share/icons/hicolor/256x256/apps/$APP.png"
cp "$BASE/resources/icon.png" "$APPDIR/$APP.png"

cp "$BASE/resources/AppRun" "$APPDIR/AppRun"
chmod +x "$APPDIR/AppRun"

cp "$BASE/resources/organizador.desktop" "$APPDIR/$APP.desktop"
cp "$BASE/resources/organizador.desktop" "$APPDIR/usr/share/applications/"

echo "AppDir pronto."

if command -v appimagetool >/dev/null 2>&1; then
    TOOL=appimagetool
elif [ -x /tmp/appimagetool ]; then
    TOOL=/tmp/appimagetool
else
    echo "appimagetool não encontrado. Baixando..."
    curl -fsSL "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -o /tmp/appimagetool
    chmod +x /tmp/appimagetool
    TOOL=/tmp/appimagetool
fi

ARCH=x86_64 "$TOOL" "$APPDIR" "$BASE/${APP}-x86_64.AppImage"
echo "AppImage gerado: $BASE/${APP}-x86_64.AppImage"
