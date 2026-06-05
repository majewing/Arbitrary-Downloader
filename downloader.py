import os

import yt_dlp


class Downloader:
    def _base_opts(self, browser=None):
        opts = {
            "quiet": True,
            "no_warnings": True,
            "remote_components": ["ejs:github"],
        }
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
        return opts

    def extract_info(self, url, browser=None):
        opts = self._base_opts(browser)
        opts["format"] = "all"
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def download(self, url, format_spec, download_dir, browser=None, progress_hook=None):
        opts = self._base_opts(browser)
        opts["format"] = format_spec
        opts["outtmpl"] = os.path.join(download_dir, "%(title)s.%(ext)s")
        opts["merge_output_format"] = "mp4"
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
