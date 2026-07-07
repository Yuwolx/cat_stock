"""과거 거래일 리포트 영구 저장소 (SQLite).

지나간 거래일의 시황/종목 데이터는 다시 수집해도 같으므로, 한 번 생성한
payload를 저장해 두고 재요청 시 크롤링·AI 칼럼 호출 없이 즉시 서빙한다.

- 텍스트는 저장하지 않는다. payload만 저장하고, 조회 시 요청자의 날짜
  맥락(요청일/보정 여부)을 덮어쓴 뒤 포매터로 다시 만든다. 이렇게 하면
  주말에 요청한 사람도 "분석 기준일 보정" 안내를 정확히 받는다.
- DB 파일은 OUTPUT_DIR(기본 output/)에 생긴다. Railway에서는 해당 경로에
  볼륨을 마운트해야 재배포 후에도 유지된다. 볼륨이 없어도 동작은 하며,
  재배포 시점에 저장분이 사라질 뿐이다.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime
from pathlib import Path

from src.utils.date_utils import KST
from src.utils.file_utils import ensure_output_dir

_DB_NAME = "cat_stock.db"
_LOCK = threading.Lock()


def _db_path() -> Path:
    return ensure_output_dir() / _DB_NAME


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            kind TEXT NOT NULL,
            key TEXT NOT NULL,
            target_date TEXT NOT NULL,
            payload TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (kind, key, target_date)
        )
        """
    )
    return conn


def is_finalized_date(target_date: str) -> bool:
    """해당 거래일 데이터가 더 이상 변하지 않는지 (오늘 이전 날짜만 True)."""
    return target_date < datetime.now(KST).strftime("%Y-%m-%d")


def load_payload(kind: str, key: str, target_date: str) -> dict | None:
    try:
        with _LOCK, _connect() as conn:
            row = conn.execute(
                "SELECT payload FROM reports WHERE kind = ? AND key = ? AND target_date = ?",
                (kind, key, target_date),
            ).fetchone()
    except Exception:
        return None
    if row is None:
        return None
    try:
        payload = json.loads(row[0])
    except (TypeError, ValueError):
        return None
    return payload if isinstance(payload, dict) else None


def save_payload(kind: str, key: str, target_date: str, payload: dict) -> None:
    try:
        serialized = json.dumps(payload, ensure_ascii=False, default=str)
        with _LOCK, _connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO reports (kind, key, target_date, payload, created_at) VALUES (?, ?, ?, ?, ?)",
                (kind, key, target_date, serialized, datetime.now(KST).isoformat()),
            )
    except Exception:
        # 저장 실패는 기능 저하일 뿐 생성 자체를 막으면 안 된다
        return
