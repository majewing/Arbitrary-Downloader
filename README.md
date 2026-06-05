# yt-dlp-demo

yt-dlp 使用笔记和常见问题解决方案。

## 常用参数

```bash
# 基本用法（查看可用格式）
yt-dlp -F <URL>

# 下载最佳画质 + 最佳音质并合并
yt-dlp -f "bestvideo+bestaudio" <URL>

# 下载指定格式（视频 + 音频分别指定 ID）
yt-dlp -f "30112+30280" <URL>

# 列出所有字幕
yt-dlp --list-subs <URL>

# 下载带字幕的视频
yt-dlp --write-subs --sub-langs all <URL>

# 下载播放列表（限制数量）
yt-dlp --playlist-end 5 <URL>

# 下载播放列表（指定范围）
yt-dlp --playlist-start 1 --playlist-end 3 <URL>

# 指定输出文件名模板
yt-dlp -o "%(title)s.%(ext)s" <URL>
# 按分类存放
yt-dlp -o "%(playlist_title)s/%(playlist_index)s-%(title)s.%(ext)s" <URL>

# 仅下载音频（提取为 mp3）
yt-dlp -x --audio-format mp3 <URL>

# 下载缩略图
yt-dlp --write-thumbnail <URL>

# 下载元数据（描述、评论等）
yt-dlp --write-info-json --write-description <URL>

# 限制下载速度
yt-dlp -r 5M <URL>
```

## Bilibili 常见问题

### HTTP 412 Precondition Failed

Bilibili 有反爬机制，直接下载会报 `HTTP 412`。解决方案：

```bash
# 从浏览器提取 Cookie 下载（推荐）
yt-dlp --cookies-from-browser chrome "https://www.bilibili.com/video/BV1Y2V66gEdn"

# 支持的浏览器：chrome, firefox, edge, brave, safari 等

# 或手动导出 Cookie 文件
yt-dlp --cookies cookies.txt "https://www.bilibili.com/video/BV1Y2V66gEdn"
```

### 其他 Bilibili 辅助参数

```bash
# 从浏览器提取 Cookie
--cookies-from-browser BROWSER

# 指定 Referer（某些视频需要）
--add-header "Referer:https://www.bilibili.com"

# 自定义 User-Agent
--user-agent "Mozilla/5.0 ..."

# 下载弹幕（需要装插件或自行处理）
```

## 合并与格式

```bash
# 默认行为：自动选择最佳视频 + 最佳音频并合并
# 合并失败时可指定合并器
--merge-output-format mp4    # 合并为 MP4
--merge-output-format mkv    # 合并为 MKV

# 不删除下载的单独音视频流（调试用）
-k
```

## 代理设置

```bash
# HTTP 代理
yt-dlp --proxy http://127.0.0.1:7890 <URL>

# 使用系统代理
yt-dlp --proxy "" <URL>
```

## 更新

```bash
# 更新 yt-dlp 到最新版（Bilibili 反爬经常变，保持最新很重要）
yt-dlp -U
```

---

# TUI 交互式视频下载器

基于 Textual 和 yt-dlp 的终端交互式下载器。

## 启动

```bash
# 安装依赖
pip install textual yt-dlp

# 运行
chmod +x run.sh && ./run.sh
# 或直接指定 Python
/Users/quming/miniconda3/bin/python main.py
```

## 使用流程

1. **输入页面** — 粘贴 Bilibili 视频链接，选择已登录的浏览器提取 Cookie
2. **格式选择** — 从列表中分别选择视频流和音频流
3. **下载页面** — 实时显示下载进度、速度、剩余时间
4. **完成** — 可打开文件夹或下载下一个视频

## 下载目录

- 默认下载到项目目录下的 `Downloads/` 文件夹
- 在格式选择页面点击「📁 更改目录」可修改
- 修改后会自动保存为新的默认路径

## 项目结构

```
yt-dlp-demo/
├── main.py                  # 入口
├── app.py                   # Textual App 主框架
├── config.py                # 配置管理（下载目录持久化）
├── downloader.py            # yt-dlp Python API 封装
├── screens/
│   ├── input_screen.py      # URL 输入 + 浏览器选择
│   ├── format_screen.py     # 视频/音频格式选择和展示
│   ├── change_path_screen.py# 修改下载目录弹窗
│   └── download_screen.py   # 下载进度和结果展示
├── config.json              # 持久化配置（自动生成）
├── main.py                  # 程序启动入口
├── run.sh                   # 启动脚本
└── requirements.txt         # Python 依赖
```
