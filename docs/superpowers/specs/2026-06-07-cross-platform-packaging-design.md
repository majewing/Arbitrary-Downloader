# 跨平台桌面打包设计

## 概述

将 yt-dlp-downloader 打包为原生桌面 GUI 应用，支持 Windows / macOS / Linux 三平台，使用 GitHub Actions CI 自动构建各平台安装包。

## 技术选型

- **GUI 框架**: PyWebView — 使用系统内置 WebView 渲染现有前端
- **打包工具**: PyInstaller — 将 Python 应用打包为独立可执行文件
- **安装包**: Windows Inno Setup (.exe) / macOS create-dmg (.dmg) / Linux AppImage
- **CI/CD**: GitHub Actions 多平台矩阵构建

## 架构

```
main.py (新入口)
├── 后台线程启动 uvicorn (FastAPI, 端口自动探测 8080→8081→...)
├── PyWebView 窗口 → http://localhost:{port}
└── 窗口关闭 → 优雅停止 uvicorn

server.py / downloader.py / config.py / database.py (零改动)
static/ (前端资源, 打包时嵌入)
```

## 新增文件

| 文件 | 说明 |
|---|---|
| `main.py` | 应用入口, PyWebView 窗口 + 后台 FastAPI |
| `app.spec` | PyInstaller 打包配置 |
| `build/windows/setup.iss` | Inno Setup 安装脚本 |
| `build/macos/create-dmg.sh` | macOS DMG 构建脚本 |
| `build/linux/AppRun` | AppImage 启动脚本 |
| `.github/workflows/build.yml` | GitHub Actions CI/CD |

## 修改文件

| 文件 | 变更 |
|---|---|
| `pyproject.toml` | 新增 pywebview、pyinstaller 依赖, 打包脚本 |

## main.py 核心逻辑

1. 在后台线程通过 `uvicorn.Server` 启动 FastAPI
2. 端口冲突时自动递增探测可用端口
3. `webview.create_window("通用视频下载器", url, width=1200, height=800, min_size=(800, 600))`
4. 绑定窗口 `closed` 事件触发 `uvicorn.should_exit = True`
5. 开发模式 (`python main.py`) 自动开启 pywebview debug

## PyInstaller 配置

- 模式: `onedir`
- 隐藏导入: `yt_dlp`, `uvicorn.logging`, `uvicorn.lifespan.on`, `uvicorn.protocols.websockets.auto`, `uvicorn.protocols.http.auto`
- 数据文件: `static/` 目录
- 运行时路径: `sys._MEIPASS` (PyInstaller) 或 `os.path.dirname(sys.executable)` 定位资源

## 三平台安装包

| 平台 | 工具 | 格式 | 特点 |
|---|---|---|---|
| Windows | Inno Setup | .exe | 安装向导, 开始菜单快捷方式, 自定义图标 |
| macOS | create-dmg | .dmg | 拖拽安装, Applications 目录 |
| Linux | appimagetool | .AppImage | 单文件, chmod +x 运行 |

## GitHub Actions 构建

```yaml
strategy:
  matrix:
    include:
      - os: windows-latest
      - os: macos-latest
      - os: ubuntu-latest
```

每个平台: checkout → 安装 Python 3.12 + uv → uv sync → pyinstaller → 构建安装包 → upload artifact

## 包体预估

| 平台 | 解压大小 | 安装包大小 |
|---|---|---|
| Windows | ~100-120MB | ~50-60MB |
| macOS | ~80-100MB | ~40-50MB |
| Linux | ~90-110MB | ~90-110MB |

## 不涉及

- 现有业务代码零改动
- 前端代码零改动
- 数据库位置不变 (`~/.video-downloader/data.db`)
