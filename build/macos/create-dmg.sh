#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
APP_NAME="ArbitraryDownloader"
EXEC_NAME="video-downloader"
DIST_DIR="$(cd "$(dirname "$0")/../.." && pwd)/dist"
DMG_DIR="$(cd "$(dirname "$0")/../.." && pwd)/dmg_staging"
DMG_OUTPUT="${DIST_DIR}/video-downloader-${VERSION}-macos.dmg"

rm -rf "${DMG_DIR}" "${DMG_OUTPUT}"
mkdir -p "${DMG_DIR}"

APP_BUNDLE="${DMG_DIR}/${APP_NAME}.app"
mkdir -p "${APP_BUNDLE}/Contents/MacOS"
mkdir -p "${APP_BUNDLE}/Contents/Resources"

cp -R "${DIST_DIR}/${EXEC_NAME}/." "${APP_BUNDLE}/Contents/MacOS/"

cat > "${APP_BUNDLE}/Contents/Info.plist" << 'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleName</key>
    <string>ArbitraryDownloader</string>
    <key>CFBundleDisplayName</key>
    <string>ArbitraryDownloader</string>
    <key>CFBundleIdentifier</key>
    <string>com.video-downloader.app</string>
    <key>CFBundleVersion</key>
    <string>0.1.0</string>
    <key>CFBundleExecutable</key>
    <string>video-downloader</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.15</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</dict>
</plist>
PLIST

ln -s /Applications "${DMG_DIR}/Applications"

hdiutil create -volname "${APP_NAME}" \
    -srcfolder "${DMG_DIR}" \
    -ov -format UDZO \
    "${DMG_OUTPUT}"

rm -rf "${DMG_DIR}"
echo "DMG created: ${DMG_OUTPUT}"
