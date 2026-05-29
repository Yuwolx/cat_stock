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
    use_mock_data: bool
    output_dir: Path


def _to_bool(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    output_dir = Path(os.getenv("OUTPUT_DIR", "output")).resolve()
    return Settings(
        app_title=os.getenv("APP_TITLE", "Jin Stock AI Research"),
        dart_api_key=os.getenv("DART_API_KEY", ""),
        use_mock_data=_to_bool(os.getenv("USE_MOCK_DATA"), default=True),
        output_dir=output_dir,
    )
