# 通用视频下载器

基于 yt-dlp 的音视频下载器，提供 Web UI 和桌面 GUI 两种使用方式，支持 YouTube、Bilibili、抖音等平台。

## 功能

- 粘贴链接自动解析视频信息（标题、时长、可用格式）
- 分别选择视频流和音频流，支持手动合并
- 实时显示下载进度、速度、剩余时间
- 支持 Bilibili Cookie 提取（解决 412 问题）
- 支持抖音视频直接下载
- 下载历史记录管理
- 多主题切换

## 快速开始

### 环境要求

- Python >= 3.12
- [uv](https://docs.astral.sh/uv/) 包管理器

### 安装

```bash
git clone https://github.com/majewing/Arbitrary-Downloader.git
cd Arbitrary-Downloader
uv sync
```

### 运行

**Web 模式（浏览器访问）：**

```bash
uv run python server.py
# 打开 http://localhost:8080
```

**桌面模式（原生窗口）：**

```bash
uv run python main.py
# 自动弹出桌面窗口
```

## 项目结构

```
├── main.py           # PyWebView 桌面入口
├── server.py         # FastAPI 服务端
├── downloader.py     # yt-dlp 下载封装
├── config.py         # 配置管理
├── database.py       # SQLite 数据库
├── app.spec          # PyInstaller 打包配置
├── static/           # 前端资源
│   ├── index.html
│   ├── style.css
│   └── app.js
├── build/            # 各平台安装包构建脚本
│   ├── windows/setup.iss
│   ├── macos/create-dmg.sh
│   └── linux/AppRun
└── .github/workflows/build.yml  # CI/CD
```

## 打包为桌面应用

项目支持打包为 Windows / macOS / Linux 原生安装包。

### 本地构建

```bash
# 安装 PyInstaller
uv add --dev pyinstaller

# 打包
uv run pyinstaller app.spec --noconfirm

# 产物在 dist/video-downloader/ 目录
```

### macOS DMG

```bash
bash build/macos/create-dmg.sh 0.1.0
# 生成 dist/video-downloader-0.1.0-macos.dmg
```

### CI 自动构建

推送到 GitHub 后，通过打 tag 触发自动构建：

```bash
git tag v0.1.0
git push origin v0.1.0
```

GitHub Actions 会自动构建三平台安装包并创建 Release。也可在 Actions 页面手动点击 "Run workflow" 触发。

## GitHub 认证配置

推送代码到 GitHub 需要配置认证，支持以下方式：

### 方式一：SSH（推荐）

1. 生成 SSH 密钥：

```bash
ssh-keygen -t ed25519 -C "你的邮箱"
```

2. 将公钥添加到 GitHub：

```bash
cat ~/.ssh/id_ed25519.pub
# 复制输出内容 → GitHub → Settings → SSH and GPG keys → New SSH key
```

3. 切换 remote 为 SSH 地址：

```bash
git remote set-url origin git@github.com:majewing/Arbitrary-Downloader.git
```

4. 测试连接并推送：

```bash
ssh -T git@github.com
git push
```

### 方式二：Personal Access Token

1. 前往 [GitHub Token 设置](https://github.com/settings/tokens)
2. 点击 "Generate new token (classic)"
3. 勾选 `repo` 权限，生成并复制 token
4. 推送时使用 token 作为密码：

```bash
git push
# Username: majewing
# Password: ghp_xxxxxxxxxxxx（粘贴 token）
```

> 密码认证已被 GitHub 废弃，必须使用 token 或 SSH。

## 数据存储

- 下载文件：默认 `~/.video-downloader/Downloads/`，可在设置中修改
- 数据库：`~/.video-downloader/data.db`
- 配置：存储在数据库中（首次运行自动从 `config.json` 迁移）
