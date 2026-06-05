import os
import subprocess
import time

from textual import work
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Label, ProgressBar, Static


def _fmt_speed(byte_per_s):
    if not byte_per_s:
        return "N/A"
    for unit in ("B/s", "KiB/s", "MiB/s", "GiB/s"):
        if byte_per_s < 1024:
            return f"{byte_per_s:.1f} {unit}"
        byte_per_s /= 1024
    return f"{byte_per_s:.1f} TiB/s"


def _fmt_size(n):
    if n is None:
        return "N/A"
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def _fmt_eta(seconds):
    if not seconds or seconds < 0:
        return "N/A"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class DownloadScreen(Screen):
    CSS = """
    Screen {
        align: center middle;
    }
    #status-container {
        width: 70%;
        min-width: 50;
        height: auto;
        padding: 1;
        border: solid $primary;
    }
    #file-title {
        text-style: bold;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    #status-label {
        width: 100%;
        text-align: center;
        margin-bottom: 1;
    }
    #progress-bar {
        margin-bottom: 1;
    }
    #info-grid {
        width: 100%;
        height: auto;
        margin-bottom: 1;
    }
    .info-item {
        width: 1fr;
    }
    .info-key {
        color: $text-muted;
    }
    .info-val {
        color: $secondary;
    }
    #complete-msg {
        text-style: bold;
        width: 100%;
        text-align: center;
        color: $success;
        margin-bottom: 1;
    }
    #btn-row {
        width: 100%;
        height: auto;
        align: center middle;
    }
    Button {
        margin: 0 1;
    }
    """

    def compose(self):
        yield Header()
        with Container(id="status-container"):
            yield Label("", id="file-title")
            yield Label("准备下载...", id="status-label")
            yield ProgressBar(total=100, show_eta=False, id="progress-bar")
            with Horizontal(id="info-grid"):
                with Container(classes="info-item"):
                    yield Label("大小", classes="info-key")
                    yield Label("", id="size-val", classes="info-val")
                with Container(classes="info-item"):
                    yield Label("速度", classes="info-key")
                    yield Label("", id="speed-val", classes="info-val")
                with Container(classes="info-item"):
                    yield Label("已下载", classes="info-key")
                    yield Label("", id="downloaded-val", classes="info-val")
                with Container(classes="info-item"):
                    yield Label("剩余时间", classes="info-key")
                    yield Label("", id="eta-val", classes="info-val")
            yield Label("", id="complete-msg")
            with Container(id="btn-row"):
                yield Button("📂 打开文件夹", id="open-folder-btn", variant="default")
                yield Button("🔄 下载另一个", id="restart-btn", variant="primary")
        yield Footer()

    def on_mount(self):
        info = self.app.video_info
        title = info.get("title", "未知标题") if info else "未知标题"
        self.query_one("#file-title", Label).update(f"⬇️  {title}")
        self.query_one("#restart-btn", Button).disabled = True
        self.query_one("#restart-btn", Button).styles.display = "none"
        self.query_one("#open-folder-btn", Button).disabled = True
        self.query_one("#open-folder-btn", Button).styles.display = "none"
        self.query_one("#complete-msg", Label).update("")
        self._start_download()

    @work(thread=True)
    def _start_download(self):
        url = self.app.video_info.get("webpage_url", "")
        if not url and self.app.video_info:
            url = f"https://www.bilibili.com/video/{self.app.video_info.get('id', '')}"
        format_spec = getattr(self.app, "download_format_spec", "bestvideo+bestaudio")
        download_dir = self.app.config.download_directory
        browser = "chrome"

        def progress_hook(d):
            self.call_from_thread(self._update_progress, d)

        try:
            self.app.downloader.download(
                url, format_spec, download_dir, browser=browser, progress_hook=progress_hook
            )
            self.call_from_thread(self._on_complete)
        except Exception as e:
            self.call_from_thread(self._on_error, str(e))

    def _update_progress(self, d):
        status = d.get("status", "")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed", 0)
            eta = d.get("eta", 0)
            pct = (downloaded / total * 100) if total else 0
            self.query_one("#status-label", Label).update("正在下载...")
            self.query_one("#progress-bar", ProgressBar).update(progress=pct)
            self.query_one("#size-val", Label).update(_fmt_size(total))
            self.query_one("#speed-val", Label).update(_fmt_speed(speed))
            self.query_one("#downloaded-val", Label).update(_fmt_size(downloaded))
            self.query_one("#eta-val", Label).update(_fmt_eta(eta))
        elif status == "finished":
            phase = "视频" if "fvideo" in d.get("filename", "") else "音视频"
            self.query_one("#status-label", Label).update(f"{phase}下载完成，正在合并...")

    def _on_complete(self):
        self.query_one("#status-label", Label).update("✅ 下载完成！")
        self.query_one("#progress-bar", ProgressBar).update(progress=100)
        self.query_one("#complete-msg", Label).update("🎉 下载完成！文件已保存到下载目录")
        self.query_one("#restart-btn", Button).disabled = False
        self.query_one("#restart-btn", Button).styles.display = "block"
        self.query_one("#open-folder-btn", Button).disabled = False
        self.query_one("#open-folder-btn", Button).styles.display = "block"

    def _on_error(self, msg):
        self.query_one("#status-label", Label).update(f"❌ 下载失败")
        self.query_one("#complete-msg", Label).update(f"错误: {msg}")
        self.query_one("#restart-btn", Button).disabled = False
        self.query_one("#restart-btn", Button).styles.display = "block"

    def on_button_pressed(self, event):
        if event.button.id == "restart-btn":
            self.app.selected_video_format = None
            self.app.selected_audio_format = None
            self.app.download_format_spec = None
            self.app.pop_screen()
            self.app.push_screen("input")
        elif event.button.id == "open-folder-btn":
            self._open_folder()

    def _open_folder(self):
        path = self.app.config.download_directory
        try:
            if os.path.exists(path):
                subprocess.Popen(["open", path])
        except OSError:
            self.notify(f"无法打开文件夹: {path}", severity="error")
