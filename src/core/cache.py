import os
import json
from typing import Any, Optional

CACHE_DIR = "cache"

def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)

def cache_path(key: str, folder: str) -> str:
    ensure_dir(os.path.join(CACHE_DIR, folder))
    return os.path.join(CACHE_DIR, folder, f"{key}.json")

def load_cache(key: str, folder: str) -> Optional[Any]:
    path = cache_path(key, folder)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return None

def save_cache(key: str, folder: str, data: Any):
    path = cache_path(key, folder)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
