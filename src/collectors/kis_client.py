from __future__ import annotations

import time

import requests

BASE_URL = "https://openapi.koreainvestment.com:9443"

# 프로세스 수명 동안 토큰 캐싱 (24시간 유효, 5분 여유)
_cache: dict = {}


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


def get_token(app_key: str, app_secret: str) -> str:
    cache_key = app_key[:8]
    entry = _cache.get(cache_key)
    if entry and entry["expires_at"] > time.time():
        return entry["token"]
    token, expires_at = _fetch_token(app_key, app_secret)
    _cache[cache_key] = {"token": token, "expires_at": expires_at}
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
