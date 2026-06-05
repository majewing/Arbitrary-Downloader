import os

from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Button, Input, Label


class ChangePathScreen(Screen):
    CSS = """
    Screen {
        align: center middle;
    }
    #dialog {
        width: 60;
        height: auto;
        padding: 2;
        border: thick $primary;
        background: $surface;
    }
    Label {
        text-style: bold;
        margin-bottom: 1;
    }
    Input {
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
    #error-msg {
        color: $error;
        height: 1;
        margin-bottom: 1;
    }
    """

    def compose(self):
        with Container(id="dialog"):
            yield Label("修改下载目录")
            yield Input(
                value=self.app.config.download_directory,
                placeholder="输入下载目录路径...",
                id="path-input",
            )
            yield Label("", id="error-msg")
            with Container(id="btn-row"):
                yield Button("确认", id="confirm-btn", variant="primary")
                yield Button("取消", id="cancel-btn")

    def on_mount(self):
        self.query_one("#path-input", Input).focus()

    def on_input_submitted(self, event):
        if event.input.id == "path-input":
            self._confirm()

    def on_button_pressed(self, event):
        if event.button.id == "confirm-btn":
            self._confirm()
        elif event.button.id == "cancel-btn":
            self.dismiss()

    def _confirm(self):
        path = self.query_one("#path-input", Input).value.strip()
        if not path:
            self.query_one("#error-msg", Label).update("⚠️ 路径不能为空")
            return
        path = os.path.abspath(os.path.expanduser(path))
        try:
            os.makedirs(path, exist_ok=True)
            self.app.config.set_download_directory(path)
            self.dismiss()
        except OSError as e:
            self.query_one("#error-msg", Label).update(f"❌ 无效路径: {e}")
