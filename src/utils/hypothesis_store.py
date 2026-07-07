"""학습 노트 가설 기록/채점 저장소.

가설을 세운 시점의 시장 스냅샷을 함께 저장해 두고, 나중에 현재 데이터와
나란히 대조하면서 사용자가 직접 판정(맞음/부분/틀림/반증됨)을 남긴다.
판정이 쌓이면 적중률이 계산된다 — 자기 판단을 시장이 채점하게 만드는
훈련 장치. report_store와 같은 SQLite 파일을 사용한다.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime

from src.utils import report_store
from src.utils.date_utils import KST

_LOCK = threading.Lock()

VERDICT_LABELS = {
    "right": "맞음",
    "partial": "부분",
    "wrong": "틀림",
    "invalidated": "반증됨",
}


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(report_store._db_path())
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS hypotheses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            note TEXT NOT NULL,
            snapshot TEXT NOT NULL,
            verdict TEXT,
            verdict_at TEXT
        )
        """
    )
    return conn


def save_hypothesis(note: dict, snapshot: dict) -> int | None:
    try:
        with _LOCK, _connect() as conn:
            cursor = conn.execute(
                "INSERT INTO hypotheses (created_at, note, snapshot) VALUES (?, ?, ?)",
                (
                    datetime.now(KST).isoformat(),
                    json.dumps(note, ensure_ascii=False, default=str),
                    json.dumps(snapshot, ensure_ascii=False, default=str),
                ),
            )
            return cursor.lastrowid
    except Exception:
        return None


def list_hypotheses(limit: int = 30) -> list[dict]:
    try:
        with _LOCK, _connect() as conn:
            rows = conn.execute(
                "SELECT id, created_at, note, snapshot, verdict, verdict_at "
                "FROM hypotheses ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
    except Exception:
        return []

    items = []
    for row in rows:
        try:
            note = json.loads(row[2])
            snapshot = json.loads(row[3])
        except (TypeError, ValueError):
            continue
        items.append(
            {
                "id": row[0],
                "created_at": row[1],
                "note": note if isinstance(note, dict) else {},
                "snapshot": snapshot if isinstance(snapshot, dict) else {},
                "verdict": row[4],
                "verdict_at": row[5],
            }
        )
    return items


def set_verdict(hypothesis_id: int, verdict: str) -> bool:
    if verdict not in VERDICT_LABELS:
        return False
    try:
        with _LOCK, _connect() as conn:
            conn.execute(
                "UPDATE hypotheses SET verdict = ?, verdict_at = ? WHERE id = ?",
                (verdict, datetime.now(KST).isoformat(), hypothesis_id),
            )
        return True
    except Exception:
        return False


def verdict_stats() -> dict:
    counts = {key: 0 for key in VERDICT_LABELS}
    total = 0
    try:
        with _LOCK, _connect() as conn:
            rows = conn.execute("SELECT verdict, COUNT(*) FROM hypotheses GROUP BY verdict").fetchall()
    except Exception:
        rows = []
    for verdict, count in rows:
        total += count
        if verdict in counts:
            counts[verdict] += count
    judged = sum(counts.values())
    return {"total": total, "judged": judged, **counts}
