import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

STATIC_DIR = "static"

datas = [(STATIC_DIR, "static")]

hiddenimports = [
    "uvicorn.logging",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.libraries",
    "uvicorn.libraries.auto",
    "yt_dlp",
    "yt_dlp.utils",
    "yt_dlp.extractor",
    "webview",
    "webview.platforms",
]

if sys.platform == "darwin":
    hiddenimports += [
        "webview.platforms.cocoa",
        "objc",
        "Foundation",
        "WebKit",
    ]
elif sys.platform == "win32":
    hiddenimports += [
        "webview.platforms.winforms",
        "clr",
    ]
else:
    hiddenimports += [
        "webview.platforms.gtk",
        "gi",
        "gi.repository",
        "gi.repository.Gtk",
        "gi.repository.WebKit",
    ]

hiddenimports += collect_submodules("yt_dlp")

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="video-downloader",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    name="video-downloader",
)

app = BUNDLE(
    coll,
    name="ArbitraryDownloader.app",
    icon=None,
    bundle_identifier="com.ytdlp.downloader",
    info_plist={
        "NSHighResolutionCapable": True,
        "CFBundleShortVersionString": "0.1.0",
    },
)
