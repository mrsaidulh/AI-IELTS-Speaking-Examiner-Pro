import json
from pathlib import Path

DESCRIPTORS_DIR = Path(__file__).parent


def load_all_descriptors() -> dict:
    descriptors = {}
    for band in [5, 6, 7, 8, 9]:
        file_path = DESCRIPTORS_DIR / f"band_{band}.json"
        if file_path.exists():
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    descriptors[f"band_{band}"] = json.load(f)
            except Exception as e:
                print(f"Error loading descriptor {file_path}: {e}")
    return descriptors


OFFICIAL_DESCRIPTORS = load_all_descriptors()
