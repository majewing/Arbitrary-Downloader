from textual.app import App

from config import Config
from downloader import Downloader


class VideoDownloaderApp(App):
    TITLE = "Bilibili Video Downloader"
    SUB_TITLE = "基于 yt-dlp"
    CSS = """
    Screen {
        background: $surface;
    }
    """

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.downloader = Downloader()
        self.video_info = None
        self.selected_video_format = None
        self.selected_audio_format = None
        self.download_format_spec = None

    def on_mount(self):
        from screens.input_screen import InputScreen

        self.push_screen(InputScreen())

    def get_screen(self, name):
        if name == "input":
            from screens.input_screen import InputScreen

            return InputScreen()
        elif name == "format":
            from screens.format_screen import FormatScreen

            return FormatScreen()
        elif name == "download":
            from screens.download_screen import DownloadScreen

            return DownloadScreen()
        elif name == "change-path":
            from screens.change_path_screen import ChangePathScreen

            return ChangePathScreen()
        return super().get_screen(name)
