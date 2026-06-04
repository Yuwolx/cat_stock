from __future__ import annotations


def format_news_item(item: object) -> str:
    if not isinstance(item, dict):
        return str(item)

    title = item.get("title") or "제목 없음"
    source = item.get("source") or item.get("broker")
    meta = ", ".join(str(part) for part in [source, item.get("date")] if part)
    title_line = f"{title} ({meta})" if meta else title
    url = item.get("url")
    return f"{title_line}\n  링크: {url}" if url else title_line
