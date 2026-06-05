import asyncio
import json
import os
import platform
import subprocess
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Query, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from config import Config
from database import Database
from downloader import Downloader

app = FastAPI(title="通用视频下载器")

STATIC_DIR = Path(__file__).parent / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

db = Database()
config = Config(db=db)
downloader = Downloader()

download_tasks: dict[str, dict] = {}


@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = STATIC_DIR / "index.html"
    return HTMLResponse(html_path.read_text(encoding="utf-8"))


@app.get("/api/config")
async def get_config():
    return {"download_directory": config.download_directory}


@app.put("/api/config")
async def update_config(body: dict):
    path = body.get("download_directory", "").strip()
    if not path:
        return JSONResponse({"error": "路径不能为空"}, status_code=400)
    path = os.path.abspath(os.path.expanduser(path))
    try:
        os.makedirs(path, exist_ok=True)
        config.set_download_directory(path)
        if "theme" in body:
            config.set_theme(body["theme"])
        return {"download_directory": config.download_directory, "theme": config.theme}
    except OSError as e:
        return JSONResponse({"error": f"无效路径: {e}"}, status_code=400)


@app.post("/api/info")
async def extract_info(body: dict):
    url = body.get("url", "").strip()
    if not url:
        return JSONResponse({"error": "请输入视频链接"}, status_code=400)
    browser = body.get("browser")
    try:
        info = await asyncio.to_thread(downloader.extract_info, url, browser)
        video_formats = []
        audio_formats = []
        for f in info.get("formats", []):
            vcodec = f.get("vcodec", "none")
            acodec = f.get("acodec", "none")
            if vcodec == "none" and acodec == "none":
                continue
            fid = f.get("format_id", "")
            ext = f.get("ext", "")
            filesize = f.get("filesize") or f.get("filesize_approx")
            size_str = _fmt_size(filesize)
            if vcodec != "none":
                height = f.get("height", 0)
                resolution = f"{height}p" if height else "N/A"
                codec = vcodec.split(".", 1)[0]
                fps = f.get("fps", "")
                fps_str = f"{fps:.0f}fps" if fps else ""
                has_audio = acodec != "none"
                video_formats.append(
                    {
                        "id": fid,
                        "resolution": resolution,
                        "ext": ext,
                        "codec": codec,
                        "fps": fps_str,
                        "size": size_str,
                        "has_audio": has_audio,
                    }
                )
            else:
                codec = acodec.split(".", 1)[0]
                abr = f.get("abr", 0)
                abr_str = f"{abr:.0f}K" if abr else "N/A"
                audio_formats.append(
                    {
                        "id": fid,
                        "ext": ext,
                        "codec": codec,
                        "abr": abr_str,
                        "size": size_str,
                    }
                )
        video_formats.sort(key=lambda x: int(x["resolution"].rstrip("p") or 0), reverse=True)
        audio_formats.sort(key=lambda x: float(x["abr"].rstrip("K") or 0), reverse=True)
        duration = info.get("duration", 0)
        return {
            "title": info.get("title", "未知标题"),
            "uploader": info.get("uploader", "未知上传者"),
            "duration": _fmt_duration(duration),
            "thumbnail": info.get("thumbnail", ""),
            "webpage_url": info.get("webpage_url", ""),
            "video_formats": video_formats,
            "audio_formats": audio_formats,
        }
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/download")
async def start_download(body: dict):
    url = body.get("url", "").strip()
    video_format = body.get("video_format", "")
    audio_format = body.get("audio_format", "")
    browser = body.get("browser")
    download_dir = body.get("download_directory", config.download_directory).strip()
    if not url:
        return JSONResponse({"error": "请输入视频链接"}, status_code=400)
    if not video_format:
        return JSONResponse({"error": "请选择视频流"}, status_code=400)
    if audio_format:
        format_spec = f"{video_format}+{audio_format}"
    else:
        format_spec = video_format
    if download_dir:
        download_dir = os.path.abspath(os.path.expanduser(download_dir))
        os.makedirs(download_dir, exist_ok=True)
    else:
        download_dir = config.download_directory

    info_title = body.get("title", "")
    info_uploader = body.get("uploader", "")
    info_thumbnail = body.get("thumbnail", "")
    info_duration = body.get("duration", "")

    history_id = db.add_history(
        {
            "url": url,
            "title": info_title,
            "uploader": info_uploader,
            "thumbnail": info_thumbnail,
            "duration": info_duration,
            "video_format": video_format,
            "audio_format": audio_format or "",
            "status": "downloading",
        }
    )

    task_id = str(uuid.uuid4())[:8]
    download_tasks[task_id] = {
        "url": url,
        "format_spec": format_spec,
        "download_dir": download_dir,
        "browser": browser,
        "history_id": history_id,
    }
    return {"task_id": task_id}


@app.websocket("/ws/download/{task_id}")
async def ws_download(websocket: WebSocket, task_id: str):
    await websocket.accept()
    if task_id not in download_tasks:
        await websocket.send_json({"status": "error", "message": "无效的任务ID"})
        await websocket.close()
        return
    task = download_tasks.pop(task_id)
    url = task["url"]
    format_spec = task["format_spec"]
    download_dir = task["download_dir"]
    browser = task["browser"]
    history_id = task["history_id"]

    progress_queue: asyncio.Queue = asyncio.Queue()

    def progress_hook(d):
        status = d.get("status", "")
        if status == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed", 0)
            eta = d.get("eta", 0)
            pct = (downloaded / total * 100) if total else 0
            progress_queue.put_nowait(
                {
                    "status": "downloading",
                    "progress": round(pct, 1),
                    "total": _fmt_size(total),
                    "downloaded": _fmt_size(downloaded),
                    "speed": _fmt_speed(speed),
                    "eta": _fmt_eta(eta),
                }
            )
        elif status == "finished":
            progress_queue.put_nowait({"status": "merging", "message": "下载完成，正在合并..."})

    download_error = None

    async def run_download():
        nonlocal download_error
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: downloader.download(url, format_spec, download_dir, browser, progress_hook),
            )
        except Exception as e:
            download_error = e

    download_task = asyncio.create_task(run_download())

    try:
        while not download_task.done():
            try:
                data = await asyncio.wait_for(progress_queue.get(), timeout=0.5)
                await websocket.send_json(data)
            except asyncio.TimeoutError:
                continue
        await download_task
        remaining = []
        while not progress_queue.empty():
            remaining.append(progress_queue.get_nowait())
        for data in remaining:
            await websocket.send_json(data)
        now = datetime.now().isoformat()
        if download_error:
            db.update_history(history_id, status="failed", error_msg=str(download_error), completed_at=now)
            await websocket.send_json({"status": "error", "message": str(download_error)})
        else:
            db.update_history(history_id, status="success", completed_at=now)
            await websocket.send_json({"status": "complete", "message": "下载完成！"})
    except WebSocketDisconnect:
        now = datetime.now().isoformat()
        db.update_history(history_id, status="failed", error_msg="客户端断开连接", completed_at=now)
    except Exception as e:
        now = datetime.now().isoformat()
        db.update_history(history_id, status="failed", error_msg=str(e), completed_at=now)
        try:
            await websocket.send_json({"status": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/api/history")
async def get_history(page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    return db.get_history(page=page, size=size)


@app.delete("/api/history/{history_id}")
async def delete_history(history_id: int):
    if db.delete_history(history_id):
        return {"ok": True}
    return JSONResponse({"error": "记录不存在"}, status_code=404)


@app.delete("/api/history")
async def clear_history():
    count = db.clear_history()
    return {"ok": True, "deleted": count}


@app.post("/api/open-folder")
async def open_folder(body: dict):
    path = body.get("path", "").strip()
    if not path:
        path = config.download_directory
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isdir(path):
        return JSONResponse({"error": "目录不存在"}, status_code=400)
    try:
        system = platform.system()
        if system == "Darwin":
            subprocess.Popen(["open", path])
        elif system == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["xdg-open", path])
        return {"ok": True}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


def _fmt_size(n):
    if n is None:
        return "N/A"
    for unit in ("B", "KiB", "MiB", "GiB"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB"


def _fmt_speed(n):
    if not n:
        return "N/A"
    for unit in ("B/s", "KiB/s", "MiB/s", "GiB/s"):
        if n < 1024:
            return f"{n:.1f} {unit}"
        n /= 1024
    return f"{n:.1f} TiB/s"


def _fmt_eta(seconds):
    if not seconds or seconds < 0:
        return "N/A"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def _fmt_duration(seconds):
    if not seconds:
        return "N/A"
    h, r = divmod(int(seconds), 3600)
    m, s = divmod(r, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server:app", host="0.0.0.0", port=8080, reload=True)
