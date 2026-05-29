from __future__ import annotations

import re
from pathlib import Path

from src.config.settings import get_settings
from src.utils.date_utils import compact_date


def ensure_output_dir() -> Path:
    output_dir = get_settings().output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def _slugify(value: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", value, flags=re.UNICODE)
    cleaned = re.sub(r"[\s-]+", "_", cleaned.strip(), flags=re.UNICODE)
    return cleaned.lower() or "output"


def save_output_text(prefix: str, target_date: str, text: str) -> Path:
    output_dir = ensure_output_dir()
    file_name = f"{_slugify(prefix)}_{compact_date(target_date)}.txt"
    target_path = output_dir / file_name
    target_path.write_text(text, encoding="utf-8")
    return target_path
