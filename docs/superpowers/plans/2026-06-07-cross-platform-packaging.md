# 跨平台桌面打包实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将 yt-dlp-downloader 打包为 Windows/macOS/Linux 三平台原生桌面 GUI 应用

**Architecture:** 新增 main.py 作为 PyWebView 桌面入口，在后台线程启动 FastAPI/uvicorn 服务，PyWebView 窗口指向 localhost。PyInstaller 打包为 onedir，再用各平台工具构建安装包。GitHub Actions CI 矩阵构建三平台产物。

**Tech Stack:** PyWebView, PyInstaller, uvicorn, FastAPI, Inno Setup, create-dmg, AppImage

---

## 文件结构

| 操作 | 文件 | 职责 |
|---|---|---|
| 创建 | `main.py` | PyWebView 桌面应用入口 |
| 创建 | `app.spec` | PyInstaller 打包配置 |
| 创建 | `build/windows/setup.iss` | Windows Inno Setup 安装脚本 |
| 创建 | `build/macos/create-dmg.sh` | macOS DMG 构建脚本 |
| 创建 | `build/linux/AppRun` | Linux AppImage 启动脚本 |
| 创建 | `.github/workflows/build.yml` | GitHub Actions CI/CD |
| 修改 | `pyproject.toml` | 新增依赖和打包脚本 |

---

### Task 1: 更新 pyproject.toml 添加新依赖

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: 添加 pywebview 依赖**

在 `dependencies` 列表中添加 `pywebview>=5.3.2`：

```toml
[project]
name = "yt-dlp-downloader"
version = "0.1.0"
description = "基于 yt-dlp 实现的音视频下载器"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.136.3",
    "pywebview>=5.3.2",
    "uvicorn[standard]>=0.49.0",
    "yt-dlp>=2026.3.17",
]

[project.scripts]
video-downloader = "main:main"

[[tool.uv.index]]
url = "https://pypi.tuna.tsinghua.edu.cn/simple"
default = true
```

- [ ] **Step 2: 同步依赖**

Run: `uv sync`

Expected: 依赖安装成功

- [ ] **Step 3: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add pywebview dependency and console script entry point"
```

---

### Task 2: 创建 main.py 桌面入口

**Files:**
- Create: `main.py`

- [ ] **Step 1: 编写 main.py**

```python
import os
import socket
import sys
import threading

import uvicorn
import webview

from server import app


def _find_free_port(start=8080, max_tries=100):
    for port in range(start, start + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError("无法找到可用端口")


def main():
    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    window = webview.create_window(
        "通用视频下载器",
        url,
        width=1200,
        height=800,
        min_size=(800, 600),
        text_select=True,
    )

    def on_closing():
        server.should_exit = True

    window.events.closing += on_closing

    webview.start(debug=bool(os.environ.get("DEBUG")))

    server.should_exit = True
    thread.join(timeout=5)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 本地测试桌面窗口启动**

Run: `uv run python main.py`

Expected: 弹出 PyWebView 桌面窗口，显示下载器界面，关闭窗口后进程正常退出

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: add PyWebView desktop application entry point"
```

---

### Task 3: 创建 PyInstaller spec 配置

**Files:**
- Create: `app.spec`

- [ ] **Step 1: 编写 app.spec**

```python
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
```

- [ ] **Step 2: 修改 server.py 中 STATIC_DIR 的路径解析以支持 PyInstaller 打包**

在 `server.py` 顶部添加资源路径辅助函数，并修改 `STATIC_DIR` 定义：

```python
import sys

def _resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent / relative_path

STATIC_DIR = _resource_path("static")
```

- [ ] **Step 3: 同样修改 config.py 中 DEFAULT_DIR 的路径解析**

在 `config.py` 中，`DEFAULT_DIR` 在打包后应指向用户目录而非 `__file__` 所在目录。修改为：

```python
DEFAULT_DIR = os.path.join(os.path.expanduser("~"), ".video-downloader", "Downloads")
```

- [ ] **Step 4: 本地测试 PyInstaller 打包**

Run: `uv run pyinstaller app.spec --noconfirm`

Expected: 生成 `dist/video-downloader/` 目录，包含可执行文件

- [ ] **Step 5: 测试打包后的可执行文件**

Run: `./dist/video-downloader/video-downloader`

Expected: 桌面窗口正常启动，下载功能可用

- [ ] **Step 6: Commit**

```bash
git add app.spec server.py config.py
git commit -m "feat: add PyInstaller spec and fix resource paths for packaging"
```

---

### Task 4: 创建 Windows 安装包构建脚本 (Inno Setup)

**Files:**
- Create: `build/windows/setup.iss`

- [ ] **Step 1: 创建 Inno Setup 脚本**

```iss
#define MyAppName "通用视频下载器"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "yt-dlp-downloader"
#define MyAppExeName "video-downloader.exe"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir=..\..\installer_output
OutputBaseFilename=video-downloader-{#MyAppVersion}-windows-x64
SetupIconFile=
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "附加选项:"; Flags: unchecked

[Files]
Source: "..\..\dist\video-downloader\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
```

- [ ] **Step 2: Commit**

```bash
git add build/windows/setup.iss
git commit -m "build: add Windows Inno Setup installer script"
```

---

### Task 5: 创建 macOS DMG 构建脚本

**Files:**
- Create: `build/macos/create-dmg.sh`

- [ ] **Step 1: 编写 DMG 构建脚本**

```bash
#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-0.1.0}"
APP_NAME="通用视频下载器"
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
    <string>通用视频下载器</string>
    <key>CFBundleDisplayName</key>
    <string>通用视频下载器</string>
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
```

- [ ] **Step 2: 添加执行权限并提交**

```bash
chmod +x build/macos/create-dmg.sh
git add build/macos/create-dmg.sh
git commit -m "build: add macOS DMG build script"
```

---

### Task 6: 创建 Linux AppImage 构建脚本

**Files:**
- Create: `build/linux/AppRun`

- [ ] **Step 1: 编写 AppRun 启动脚本**

```bash
#!/usr/bin/env bash
SELF=$(readlink -f "$0")
HERE=${SELF%/*}
export PATH="${HERE}/usr/bin:${PATH}"
exec "${HERE}/video-downloader" "$@"
```

- [ ] **Step 2: 添加执行权限并提交**

```bash
chmod +x build/linux/AppRun
git add build/linux/AppRun
git commit -m "build: add Linux AppImage AppRun script"
```

---

### Task 7: 创建 GitHub Actions CI/CD

**Files:**
- Create: `.github/workflows/build.yml`

- [ ] **Step 1: 编写 GitHub Actions 工作流**

```yaml
name: Build Desktop App

on:
  push:
    tags:
      - "v*"
  workflow_dispatch:

jobs:
  build:
    strategy:
      fail-fast: false
      matrix:
        include:
          - os: windows-latest
            platform: windows
            ext: exe
          - os: macos-latest
            platform: macos
            ext: dmg
          - os: ubuntu-latest
            platform: linux
            ext: AppImage

    runs-on: ${{ matrix.os }}

    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.12

      - name: Install dependencies
        run: uv sync

      - name: Build with PyInstaller (Linux)
        if: matrix.platform == 'linux'
        run: |
          sudo apt-get update
          sudo apt-get install -y libglib2.0-0 libgdk-pixbuf2.0-0 libwebkit2gtk-4.1-dev
          uv run pyinstaller app.spec --noconfirm

      - name: Build with PyInstaller (Windows/macOS)
        if: matrix.platform != 'linux'
        run: uv run pyinstaller app.spec --noconfirm

      - name: Build Windows installer
        if: matrix.platform == 'windows'
        run: |
          curl -L -o iscc.exe https://files.jrsoftware.org/is/6/ISCC.exe
          ./iscc.exe build/windows/setup.iss
          mv installer_output/*.exe dist/video-downloader-windows-x64.exe

      - name: Build macOS DMG
        if: matrix.platform == 'macos'
        run: bash build/macos/create-dmg.sh "${{ github.ref_name }}"

      - name: Build Linux AppImage
        if: matrix.platform == 'linux'
        run: |
          VERSION="${GITHUB_REF_NAME:-0.1.0}"
          APPDIR="dist/appdir"
          mkdir -p "${APPDIR}/usr/bin"
          cp -r dist/video-downloader/* "${APPDIR}/usr/bin/"
          cp build/linux/AppRun "${APPDIR}/AppRun"
          chmod +x "${APPDIR}/AppRun"
          cat > "${APPDIR}/video-downloader.desktop" << EOF
          [Desktop Entry]
          Name=通用视频下载器
          Exec=video-downloader
          Type=Application
          Categories=Utility;
          EOF
          wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage" -O appimagetool
          chmod +x appimagetool
          ./appimagetool "${APPDIR}" "dist/video-downloader-${VERSION}-linux-x86_64.AppImage"

      - name: Upload artifacts
        uses: actions/upload-artifact@v4
        with:
          name: video-downloader-${{ matrix.platform }}
          path: |
            dist/*.exe
            dist/*.dmg
            dist/*.AppImage

  release:
    needs: build
    runs-on: ubuntu-latest
    if: startsWith(github.ref, 'refs/tags/v')
    permissions:
      contents: write
    steps:
      - name: Download all artifacts
        uses: actions/download-artifact@v4
        with:
          path: artifacts

      - name: Create GitHub Release
        uses: softprops/action-gh-release@v2
        with:
          files: artifacts/**/*
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/build.yml
git commit -m "ci: add GitHub Actions cross-platform build workflow"
```

---

### Task 8: 更新 .gitignore 并最终验证

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 在 .gitignore 中添加构建产物忽略规则**

追加以下内容：

```
# Build artifacts
installer_output/
dmg_staging/
dist/appdir/
*.spec.bak
```

- [ ] **Step 2: 本地完整验证流程**

Run: `uv run python main.py`

Expected: 桌面窗口正常启动，所有功能正常

- [ ] **Step 3: Commit**

```bash
git add .gitignore
git commit -m "chore: update .gitignore for build artifacts"
```
