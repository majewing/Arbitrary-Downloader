from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Footer, Header, Label, Static


def _fmt_size(bytes_val):
    if bytes_val is None:
        return "N/A"
    for unit in ("B", "KiB", "MiB", "GiB"):
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TiB"


def _fmt_duration(seconds):
    if not seconds:
        return "N/A"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


class FormatScreen(Screen):
    CSS = """
    #header-info {
        height: auto;
        padding: 0 1;
        margin-bottom: 1;
    }
    #title-text {
        text-style: bold;
        width: 100%;
    }
    #meta-text {
        color: $text-muted;
        width: 100%;
    }
    #tables-container {
        height: 1fr;
    }
    #video-section, #audio-section {
        height: 1fr;
        border: solid $primary;
        margin: 0 1 1 1;
        padding: 0 1;
    }
    .section-title {
        text-style: bold;
        background: $primary;
        color: $text;
        padding: 0 1;
        margin-bottom: 1;
    }
    .section-hint {
        color: $text-muted;
        text-style: italic;
    }
    DataTable {
        height: 1fr;
    }
    #bottom-bar {
        dock: bottom;
        height: auto;
        padding: 1;
        background: $panel;
        border-top: solid $primary;
    }
    #path-display {
        width: 1fr;
        margin-right: 1;
    }
    #path-label {
        color: $text-muted;
    }
    #path-value {
        color: $secondary;
    }
    #action-buttons {
        width: auto;
    }
    Button {
        margin-left: 1;
    }
    #no-video-msg, #no-audio-msg {
        color: $text-muted;
        text-align: center;
        height: 3;
    }
    """

    def compose(self):
        yield Header()
        yield Container(id="header-info")
        with Container(id="tables-container"):
            with Vertical(id="video-section"):
                yield Label("🎬 视频流 (选择一个)", classes="section-title")
                yield DataTable(id="video-table", cursor_type="row")
                yield Label("没有可用视频流", id="no-video-msg")
            with Vertical(id="audio-section"):
                yield Label("🎵 音频流 (选择一个)", classes="section-title")
                yield DataTable(id="audio-table", cursor_type="row")
                yield Label("没有可用音频流", id="no-audio-msg")
        with Container(id="bottom-bar"):
            with Container(id="path-display"):
                yield Label("下载目录", id="path-label")
                yield Label("", id="path-value")
            with Container(id="action-buttons"):
                yield Button("📁 更改目录", id="change-path-btn")
                yield Button("⬇️ 下载", id="download-btn", variant="primary")
                yield Button("🔙 返回", id="back-btn")
        yield Footer()

    def on_mount(self):
        info = self.app.video_info
        if not info:
            return

        header = self.query_one("#header-info", Container)
        title = info.get("title", "未知标题")
        uploader = info.get("uploader", "未知上传者")
        duration = info.get("duration", 0)
        header.mount(
            Static(title, id="title-text"),
            Static(f"{uploader}  |  时长: {_fmt_duration(duration)}", id="meta-text"),
        )

        formats = info.get("formats", [])
        video_rows = []
        audio_rows = []
        for f in formats:
            vcodec = f.get("vcodec", "none")
            acodec = f.get("acodec", "none")
            if vcodec == "none" and acodec == "none":
                continue
            fid = f.get("format_id", "")
            ext = f.get("ext", "")
            size = _fmt_size(f.get("filesize") or f.get("filesize_approx"))
            if vcodec != "none" and acodec != "none":
                height = f.get("height", 0)
                resolution = f"{height}p" if height else "N/A"
                codec = vcodec.split(".", 1)[0]
                fps = f.get("fps", "")
                fps_str = f"{fps:.0f}fps" if fps else ""
                video_rows.append((fid, resolution, ext, codec, fps_str, size, "✔︎ 含音频"))
            elif vcodec != "none":
                height = f.get("height", 0)
                resolution = f"{height}p" if height else "N/A"
                codec = vcodec.split(".", 1)[0]
                fps = f.get("fps", "")
                fps_str = f"{fps:.0f}fps" if fps else ""
                video_rows.append((fid, resolution, ext, codec, fps_str, size, ""))
            else:
                codec = acodec.split(".", 1)[0]
                abr = f.get("abr", 0)
                abr_str = f"{abr:.0f}K" if abr else "N/A"
                audio_rows.append((fid, ext, codec, abr_str, size))

        video_rows.sort(key=lambda r: int(r[1].rstrip("p") or 0), reverse=True)
        audio_rows.sort(key=lambda r: float(r[3].rstrip("K") or 0), reverse=True)

        vt = self.query_one("#video-table", DataTable)
        vt.add_columns("ID", "分辨率", "格式", "编码", "FPS", "大小", "备注")
        if video_rows:
            vt.add_rows(video_rows)
            vt.focus()
            self.query_one("#no-video-msg", Label).remove()
        else:
            self.query_one("#no-video-msg", Label).update("⚠️ 无可用视频流")

        at = self.query_one("#audio-table", DataTable)
        at.add_columns("ID", "格式", "编码", "码率", "大小")
        if audio_rows:
            at.add_rows(audio_rows)
            self.query_one("#no-audio-msg", Label).remove()
        else:
            self.query_one("#no-audio-msg", Label).update("⚠️ 无可用音频流")

        self.query_one("#path-value", Label).update(self.app.config.download_directory)

    def on_data_table_row_selected(self, event):
        table = event.data_table
        row = table.get_row(event.row_key)
        fid = row[0]
        if table.id == "video-table":
            self.app.selected_video_format = fid
        elif table.id == "audio-table":
            self.app.selected_audio_format = fid

    def on_button_pressed(self, event):
        if event.button.id == "download-btn":
            self._start_download()
        elif event.button.id == "change-path-btn":
            self.app.push_screen("change-path")
        elif event.button.id == "back-btn":
            self.app.pop_screen()

    def _start_download(self):
        video_fid = self.app.selected_video_format
        audio_fid = self.app.selected_audio_format
        if not video_fid and not audio_fid:
            self.notify("请先选择视频流和音频流", severity="error")
            return
        if not video_fid:
            self.notify("请选择视频流", severity="error")
            return
        if audio_fid:
            format_spec = f"{video_fid}+{audio_fid}"
        else:
            format_spec = video_fid
        self.app.download_format_spec = format_spec
        self.app.push_screen("download")
