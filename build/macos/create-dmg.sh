#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
APP_NAME="ArbitraryDownloader"
DIST_DIR="$(cd "$(dirname "$0")/../.." && pwd)/dist"
DMG_DIR="$(cd "$(dirname "$0")/../.." && pwd)/dmg_staging"
DMG_OUTPUT="${DIST_DIR}/video-downloader-${VERSION}-macos.dmg"

APP_BUNDLE="${DIST_DIR}/${APP_NAME}.app"

if [ ! -d "${APP_BUNDLE}" ]; then
    echo "Error: ${APP_BUNDLE} not found. Run PyInstaller first."
    exit 1
fi

rm -rf "${DMG_DIR}" "${DMG_OUTPUT}"
mkdir -p "${DMG_DIR}"

cp -R "${APP_BUNDLE}" "${DMG_DIR}/"
ln -s /Applications "${DMG_DIR}/Applications"

hdiutil create -volname "${APP_NAME}" \
    -srcfolder "${DMG_DIR}" \
    -ov -format UDZO \
    "${DMG_OUTPUT}"

rm -rf "${DMG_DIR}"
echo "DMG created: ${DMG_OUTPUT}"
