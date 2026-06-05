from textual import work
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, Input, Label, Select, Static


class InputScreen(Screen):
    CSS = """
    Screen {
        align: center middle;
    }
    #input-container {
        width: 70%;
        min-width: 50;
        height: auto;
        padding: 1;
    }
    #title-label {
        text-style: bold;
        width: 100%;
        text-align: center;
        margin-bottom: 1;
        color: $primary;
    }
    #url-input {
        margin-bottom: 1;
    }
    #browser-select {
        margin-bottom: 1;
    }
    Button {
        width: 100%;
    }
    #tip {
        color: $text-muted;
        margin-top: 1;
        text-align: center;
    }
    #error-msg {
        color: $error;
        text-align: center;
        margin-top: 1;
        height: 3;
    }
    """

    def compose(self):
        yield Header()
        with Container(id="input-container"):
            yield Label("Bilibili 视频下载器", id="title-label")
            yield Input(placeholder="输入 Bilibili 视频链接...", id="url-input")
            yield Select(
                [(b.title(), b) for b in ["chrome", "firefox", "edge", "brave", "safari"]],
                prompt="选择浏览器提取 Cookie",
                id="browser-select",
                value="chrome",
            )
            yield Button("获取视频信息", id="fetch-btn", variant="primary")
            yield Static("", id="error-msg")
            yield Static("💡 提示：需要先在浏览器中登录 Bilibili，选你已登录的浏览器", id="tip")
        yield Footer()

    def on_mount(self):
        self.query_one("#url-input", Input).focus()

    def on_button_pressed(self, event):
        if event.button.id == "fetch-btn":
            self._start_fetch()

    def on_input_submitted(self, event):
        if event.input.id == "url-input":
            self._start_fetch()

    def _start_fetch(self):
        url_input = self.query_one("#url-input", Input)
        url = url_input.value.strip()
        if not url:
            self.query_one("#error-msg", Static).update("⚠️ 请输入视频链接")
            url_input.focus()
            return
        self.query_one("#error-msg", Static).update("")
        btn = self.query_one("#fetch-btn", Button)
        btn.disabled = True
        btn.label = "正在获取..."
        self.fetch_video_info(url)

    @work(thread=True)
    def fetch_video_info(self, url):
        browser = self.query_one("#browser-select", Select).value
        try:
            info = self.app.downloader.extract_info(url, browser)
            self.app.video_info = info
            self.app.call_from_thread(self._on_success)
        except Exception as e:
            self.app.call_from_thread(self._on_error, str(e))

    def _on_success(self):
        self.app.push_screen("format")

    def _on_error(self, msg):
        self.query_one("#fetch-btn", Button).disabled = False
        self.query_one("#fetch-btn", Button).label = "获取视频信息"
        self.query_one("#error-msg", Static).update(f"❌ 获取失败: {msg}")
