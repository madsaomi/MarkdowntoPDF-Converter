"""Простой офлайн-кэш для внешних рендеров (LaTeX/диаграммы).

Храним в кеше по хешу, чтобы при повторе не ходить во внешние сервисы.
Кэш не обязателен — если запись не найдена, используем существующий путь.
"""

import hashlib
import json
import os
from typing import Any, Optional


def _cache_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, "MarkdownToPDF", "render_cache")
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass
    return path


def _key(prefix: str, data: str) -> str:
    h = hashlib.sha256(data.encode("utf-8", errors="ignore")).hexdigest()
    return f"{prefix}_{h}.json"


def get_cached(prefix: str, data: str) -> Optional[dict[str, Any]]:
    try:
        p = os.path.join(_cache_dir(), _key(prefix, data))
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def set_cached(prefix: str, data: str, payload: dict[str, Any]) -> bool:
    try:
        p = os.path.join(_cache_dir(), _key(prefix, data))
        with open(p, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False)
        return True
    except Exception:
        return False
