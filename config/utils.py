import json
import os
import re
import time
from typing import Any, Optional

def to_lowercase_if_needed(text: str, enabled: bool = True) -> str:
    return text.lower() if enabled else text

def clean_spaces(text: str) -> str:
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def cache_get(cache_path: str, ttl_s: int) -> Optional[Any]:
    try:
        if not os.path.exists(cache_path):
            return None
        age = time.time() - os.path.getmtime(cache_path)
        if age > ttl_s:
            return None
        with open(cache_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None

def cache_set(cache_path: str, obj: Any) -> None:
    ensure_dir(os.path.dirname(cache_path))
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(obj, f)
