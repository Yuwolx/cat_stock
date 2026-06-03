import pytest

from src.config.settings import get_settings
from src.services.column_service import _split_title_body, generate_market_column
from src.ui.dashboard import _column_html


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_generate_market_column_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    result = generate_market_column(
        {
            "target_date": "2026-06-03",
            "indices": {},
            "global_macro": {},
            "investor_flows": {},
            "market_events": {},
            "sectors": [],
        }
    )

    assert result == {
        "is_available": False,
        "reason": "missing_api_key",
        "title": None,
        "body": None,
    }


def test_split_title_body_with_separator() -> None:
    result = _split_title_body("시장 방향성 재점검\n---\n본문입니다.", "기본 제목")

    assert result == {"title": "시장 방향성 재점검", "body": "본문입니다."}


def test_split_title_body_without_separator() -> None:
    result = _split_title_body("시장 방향성 재점검\n본문입니다.", "기본 제목")

    assert result == {"title": "시장 방향성 재점검", "body": "본문입니다."}


@pytest.mark.parametrize(
    ("reason", "message"),
    [
        ("missing_api_key", "AI 칼럼: ANTHROPIC_API_KEY가 설정되지 않았습니다."),
        ("package_missing", "AI 칼럼: anthropic 패키지가 설치되지 않았습니다."),
        ("api_error", "AI 칼럼: 생성 중 오류가 발생했습니다."),
    ],
)
def test_column_html_renders_reason_message(reason: str, message: str) -> None:
    html = _column_html(
        {
            "is_available": False,
            "reason": reason,
            "title": None,
            "body": None,
        },
        "2026-06-03",
    )

    assert message in html
