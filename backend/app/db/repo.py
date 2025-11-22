import json
from pathlib import Path


class Repo:
    def __init__(self):
        self.data_path = Path(__file__).parent.parent / "data" / "lego_components.json"

    def get_all_components(self):
        if not self.data_path.exists():
            print(f"[WARN] JSON-файл {self.data_path} не знайдено")
            return []
        with open(self.data_path, "r", encoding="utf-8") as f:
            return json.load(f)
