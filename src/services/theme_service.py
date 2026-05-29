from __future__ import annotations

from src.collectors.theme.naver_theme_collector import get_theme_stocks
from src.collectors.theme.news_collector import get_theme_news
from src.collectors.theme.peer_collector import get_theme_peers
from src.config.settings import get_settings
from src.formatters.theme_formatter import format_theme_report
from src.utils.date_utils import today_kst_string
from src.utils.file_utils import save_output_text


def generate_theme_report(theme_name: str, use_mock_data: bool | None = None) -> dict:
    settings = get_settings()
    target_date = today_kst_string()
    effective_mock_data = settings.use_mock_data if use_mock_data is None else use_mock_data
    payload = {
        "target_date": target_date,
        "is_mock_data": effective_mock_data,
        "theme_name": theme_name,
        "stocks": get_theme_stocks(theme_name, use_mock_data=effective_mock_data),
        "news_bundle": get_theme_news(theme_name, use_mock_data=effective_mock_data),
        "peer_bundle": get_theme_peers(
            theme_name,
            api_key=settings.dart_api_key,
            use_mock_data=effective_mock_data,
        ),
    }
    text = format_theme_report(payload)
    path = save_output_text(f"theme_{theme_name}", target_date, text)
    return {"text": text, "path": path, "payload": payload}
