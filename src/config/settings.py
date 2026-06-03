from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    app_title: str
    dart_api_key: str
    kis_app_key: str
    kis_app_secret: str
    openai_api_key: str
    output_dir: Path


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    output_dir = Path(os.getenv("OUTPUT_DIR", "output")).resolve()
    return Settings(
        app_title=os.getenv("APP_TITLE", "cat_stock"),
        dart_api_key=os.getenv("DART_API_KEY", "").strip(),
        kis_app_key=os.getenv("KIS_APP_KEY", "").strip(),
        kis_app_secret=os.getenv("KIS_APP_SECRET", "").strip(),
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        output_dir=output_dir,
    )
