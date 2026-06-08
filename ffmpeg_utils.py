import os
import platform
import shutil
import sys
import tarfile
import tempfile
import urllib.request
import zipfile

BIN_DIR = os.path.join(os.path.expanduser("~"), ".video-downloader", "bin")


def _ffmpeg_name():
    return "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"


def ensure_ffmpeg():
    if shutil.which("ffmpeg"):
        return None

    local = os.path.join(BIN_DIR, _ffmpeg_name())
    if os.path.isfile(local):
        return BIN_DIR

    os.makedirs(BIN_DIR, exist_ok=True)

    system = platform.system()
    machine = platform.machine()
    try:
        if system == "Darwin":
            _download_macos(machine)
        elif system == "Windows":
            _download_windows()
        else:
            _download_linux(machine)
    except Exception:
        return None

    return BIN_DIR


def _download_macos(machine):
    url = "https://evermeet.cx/ffmpeg/getrelease/zip"
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "ffmpeg.zip")
        urllib.request.urlretrieve(url, zip_path)
        with zipfile.ZipFile(zip_path) as zf:
            for name in zf.namelist():
                if name.lower().endswith("ffmpeg") and not name.endswith("/"):
                    with zf.open(name) as src:
                        with open(os.path.join(BIN_DIR, "ffmpeg"), "wb") as dst:
                            dst.write(src.read())
                    break
    ffmpeg = os.path.join(BIN_DIR, "ffmpeg")
    if os.path.isfile(ffmpeg):
        os.chmod(ffmpeg, 0o755)


def _download_windows():
    url = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = os.path.join(tmp, "ffmpeg.zip")
        urllib.request.urlretrieve(url, zip_path)
        ffmpeg_target = os.path.join(BIN_DIR, "ffmpeg.exe")
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.namelist():
                if member.endswith("/bin/ffmpeg.exe"):
                    with zf.open(member) as src:
                        with open(ffmpeg_target, "wb") as dst:
                            dst.write(src.read())
                    break


def _download_linux(machine):
    arch = "arm64" if machine in ("aarch64", "arm64") else "amd64"
    url = f"https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-{arch}-static.tar.xz"
    with tempfile.TemporaryDirectory() as tmp:
        tar_path = os.path.join(tmp, "ffmpeg.tar.xz")
        urllib.request.urlretrieve(url, tar_path)
        with tarfile.open(tar_path, "r:xz") as tf:
            for member in tf.getmembers():
                if member.name.endswith("/ffmpeg"):
                    member.name = "ffmpeg"
                    tf.extract(member, BIN_DIR)
                    break
    ffmpeg = os.path.join(BIN_DIR, "ffmpeg")
    if os.path.isfile(ffmpeg):
        os.chmod(ffmpeg, 0o755)
