from __future__ import annotations

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary.asp",
}


def get_fnguide_reports(code: str, from_date: str, to_date: str) -> list[dict]:
    """
    code: 6-digit stock code (e.g. '005930')
    from_date / to_date: YYYYMMDD strings
    Returns list of {date, title, summary, broker}
    """
    gicode = f"A{code}"
    url = "https://comp.fnguide.com/SVO2/ASP/SVD_Report_Summary_Data.asp"
    params = {"gicode": gicode, "fr_dt": from_date, "to_dt": to_date, "check": "all", "stext": ""}
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except Exception:
        return []

    soup = BeautifulSoup(resp.text, "html.parser")
    results = []
    for row in soup.select("tr"):
        title_tag = row.select_one("dl.um_tdinsm dt")
        if not title_tag:
            continue
        code_tag = title_tag.select_one("span.txt1")
        if not code_tag or code_tag.get_text(strip=True) != gicode:
            continue

        dt_tag = row.select_one("td.clf")
        body_tags = row.select("dl.um_tdinsm dd")
        broker_tag = row.select_one("td.cle span.gpbox")

        date_str = dt_tag.get_text(strip=True) if dt_tag else ""
        title_span = title_tag.select_one("span.txt2")
        title = title_span.get_text(strip=True).lstrip("-").strip() if title_span else ""
        summary = " / ".join(dd.get_text(strip=True) for dd in body_tags if dd.get_text(strip=True))
        broker = broker_tag.get_text(separator=" ", strip=True) if broker_tag else ""

        results.append({"date": date_str, "title": title, "summary": summary, "broker": broker})

    return results
