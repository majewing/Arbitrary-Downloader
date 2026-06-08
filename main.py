import os
import socket
import sys
import threading

import uvicorn
import webview

from server import app


def _find_free_port(start=8080, max_tries=100):
    for port in range(start, start + max_tries):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("127.0.0.1", port))
                return port
        except OSError:
            continue
    raise RuntimeError("无法找到可用端口")


def main():
    port = _find_free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    url = f"http://127.0.0.1:{port}"
    window = webview.create_window(
        "ArbitraryDownloader",
        url,
        width=1200,
        height=800,
        min_size=(800, 600),
        text_select=True,
    )

    def on_closing():
        server.should_exit = True

    window.events.closing += on_closing

    webview.start(debug=bool(os.environ.get("DEBUG")))

    server.should_exit = True
    thread.join(timeout=5)


if __name__ == "__main__":
    main()
