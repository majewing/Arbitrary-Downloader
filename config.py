import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
DEFAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")


class Config:
    def __init__(self):
        self.download_directory = DEFAULT_DIR
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as f:
                    data = json.load(f)
                self.download_directory = data.get("download_directory", DEFAULT_DIR)
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        with open(CONFIG_FILE, "w") as f:
            json.dump({"download_directory": self.download_directory}, f, indent=2)

    def set_download_directory(self, path):
        path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(path, exist_ok=True)
        self.download_directory = path
        self.save()
