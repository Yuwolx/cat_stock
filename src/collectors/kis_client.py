from __future__ import annotations

import json
import time
from pathlib import Path

import requests

BASE_URL = "https://openapi.koreainvestment.com:9443"

# 메모리 캐시 (동일 프로세스 내)
_mem_cache: dict = {}

# 파일 캐시 경로 — output/ 아래에 저장 (.gitignore에 이미 포함)
_TOKEN_FILE = Path(__file__).parent.parent.parent / "output" / ".kis_token_cache.json"


def _fetch_token(app_key: str, app_secret: str) -> tuple[str, float]:
    resp = requests.post(
        f"{BASE_URL}/oauth2/tokenP",
        json={
            "grant_type": "client_credentials",
            "appkey": app_key,
            "appsecret": app_secret,
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    token = data["access_token"]
    expires_at = time.time() + int(data.get("expires_in", 86400)) - 300
    return token, expires_at


def _load_file_cache(cache_key: str) -> dict | None:
    try:
        if _TOKEN_FILE.exists():
            data = json.loads(_TOKEN_FILE.read_text())
            entry = data.get(cache_key)
            if entry and entry.get("expires_at", 0) > time.time():
                return entry
    except Exception:
        pass
    return None


def _save_file_cache(cache_key: str, token: str, expires_at: float) -> None:
    try:
        _TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
        existing: dict = {}
        if _TOKEN_FILE.exists():
            try:
                existing = json.loads(_TOKEN_FILE.read_text())
            except Exception:
                pass
        existing[cache_key] = {"token": token, "expires_at": expires_at}
        _TOKEN_FILE.write_text(json.dumps(existing))
    except Exception:
        pass


def get_token(app_key: str, app_secret: str) -> str:
    cache_key = app_key[:8]

    # 1. 메모리 캐시
    entry = _mem_cache.get(cache_key)
    if entry and entry["expires_at"] > time.time():
        return entry["token"]

    # 2. 파일 캐시 (프로세스 재시작 후에도 유지)
    file_entry = _load_file_cache(cache_key)
    if file_entry:
        _mem_cache[cache_key] = file_entry
        return file_entry["token"]

    # 3. 신규 발급
    token, expires_at = _fetch_token(app_key, app_secret)
    _mem_cache[cache_key] = {"token": token, "expires_at": expires_at}
    _save_file_cache(cache_key, token, expires_at)
    return token


def kis_get(
    path: str,
    tr_id: str,
    params: dict,
    app_key: str,
    app_secret: str,
) -> dict:
    token = get_token(app_key, app_secret)
    resp = requests.get(
        f"{BASE_URL}{path}",
        headers={
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": app_key,
            "appsecret": app_secret,
            "tr_id": tr_id,
        },
        params=params,
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
