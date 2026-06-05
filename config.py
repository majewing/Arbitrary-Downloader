import os

from database import DB_DIR

DEFAULT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Downloads")


class Config:
    def __init__(self, db=None):
        from database import Database

        self._db = db or Database()
        self._migrate_json()

    def _migrate_json(self):
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        if os.path.exists(json_path) and self._db.get_config("migrated_from_json") is None:
            try:
                import json

                with open(json_path) as f:
                    data = json.load(f)
                if "download_directory" in data:
                    self._db.set_config("download_directory", data["download_directory"])
                self._db.set_config("migrated_from_json", "1")
            except Exception:
                pass

    @property
    def download_directory(self):
        return self._db.get_config("download_directory", DEFAULT_DIR)

    def set_download_directory(self, path):
        path = os.path.abspath(os.path.expanduser(path))
        os.makedirs(path, exist_ok=True)
        self._db.set_config("download_directory", path)
