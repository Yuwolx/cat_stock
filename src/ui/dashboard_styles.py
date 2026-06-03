from __future__ import annotations

from pathlib import Path


DISPATCH_CSS = Path(__file__).with_name("dashboard.css").read_text(encoding="utf-8")
