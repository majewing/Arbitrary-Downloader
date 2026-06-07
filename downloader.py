import os
import re
import urllib.request
import urllib.parse

import yt_dlp

_DOUYIN_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?douyin\.com/video/(\d+)")
_MOBILE_UA = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"


def is_douyin_url(url):
    return bool(_DOUYIN_PATTERN.match(url.strip()))


def _extract_douyin_id(url):
    m = _DOUYIN_PATTERN.match(url.strip())
    return m.group(1) if m else None


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
        if is_douyin_url(url):
            return self._extract_douyin_info(url)
        opts = self._base_opts(browser)
        opts["format"] = "all"
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def download(self, url, format_spec, download_dir, browser=None, progress_hook=None):
        if is_douyin_url(url):
            self._download_douyin(url, format_spec, download_dir, progress_hook)
            return
        opts = self._base_opts(browser)
        opts["format"] = format_spec
        opts["outtmpl"] = os.path.join(download_dir, "%(title)s.%(ext)s")
        opts["merge_output_format"] = "mp4"
        if progress_hook:
            opts["progress_hooks"] = [progress_hook]
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])

    def _extract_douyin_info(self, url):
        video_id = _extract_douyin_id(url)
        if not video_id:
            raise ValueError("无法从 URL 中提取抖音视频 ID")

        share_url = f"https://www.iesdouyin.com/share/video/{video_id}"
        headers = {"User-Agent": _MOBILE_UA, "Accept": "text/html"}
        req = urllib.request.Request(share_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=15)
        body = resp.read().decode("utf-8")

        desc_match = re.search(r'"desc"\s*:\s*"([^"]+)"', body)
        nickname_match = re.search(r'"nickname"\s*:\s*"([^"]+)"', body)
        cover_match = re.search(r'"cover"\s*:\s*\{[^}]*"url_list"\s*:\s*\["([^"]+)"', body)
        vid_match = re.search(r"video_id=([a-zA-Z0-9_-]+)", body)

        if not vid_match:
            raise ValueError("无法从抖音页面中提取视频信息，请检查链接是否正确")

        play_video_id = vid_match.group(1)
        play_url = f"https://aweme.snssdk.com/aweme/v1/play/?video_id={play_video_id}&ratio=720p&line=0"

        req2 = urllib.request.Request(play_url, headers={"User-Agent": _MOBILE_UA}, method="HEAD")
        resp2 = urllib.request.urlopen(req2, timeout=15)
        final_url = resp2.url
        content_length = int(resp2.headers.get("Content-Length", 0))

        title = desc_match.group(1) if desc_match else f"抖音视频_{video_id}"
        uploader = nickname_match.group(1) if nickname_match else "未知"
        thumbnail = ""
        if cover_match:
            thumbnail = cover_match.group(1).replace("\\u002F", "/")

        return {
            "title": title,
            "uploader": uploader,
            "duration": 0,
            "thumbnail": thumbnail,
            "webpage_url": url,
            "douyin_direct_url": final_url,
            "douyin_file_size": content_length,
            "formats": [
                {
                    "format_id": "douyin_direct",
                    "ext": "mp4",
                    "height": 720,
                    "vcodec": "h264",
                    "acodec": "aac",
                    "filesize": content_length,
                    "url": final_url,
                }
            ],
        }

    def _download_douyin(self, url, format_spec, download_dir, progress_hook=None):
        info = self._extract_douyin_info(url)
        direct_url = info.get("douyin_direct_url")
        if not direct_url:
            raise ValueError("无法获取抖音视频直链")

        title = info["title"].replace("/", "_").replace("\\", "_").replace(":", "_")
        filename = "".join(c for c in title if c not in '\'"<>|?*')[:200]
        filepath = os.path.join(download_dir, f"{filename}.mp4")

        headers = {"User-Agent": _MOBILE_UA}
        req = urllib.request.Request(direct_url, headers=headers)
        resp = urllib.request.urlopen(req, timeout=60)

        total = int(resp.headers.get("Content-Length", 0))
        downloaded = 0
        chunk_size = 8192

        with open(filepath, "wb") as f:
            while True:
                chunk = resp.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if progress_hook and total:
                    progress_hook({
                        "status": "downloading",
                        "total_bytes": total,
                        "downloaded_bytes": downloaded,
                        "speed": 0,
                        "eta": 0,
                    })

        if progress_hook:
            progress_hook({"status": "finished", "filename": filepath})
