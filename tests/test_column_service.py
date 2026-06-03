import builtins
import sys
from types import ModuleType, SimpleNamespace

import pytest

from src.config.settings import get_settings
from src.services.column_service import _call_gpt, _split_title_body, generate_market_column
from src.ui.dashboard import _column_html


@pytest.fixture(autouse=True)
def clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_generate_market_column_missing_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

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


def test_call_gpt_returns_text_with_fake_openai_client(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResponses:
        @staticmethod
        def create(model: str, input: str, max_output_tokens: int) -> SimpleNamespace:
            assert model == "gpt-4o-mini"
            assert input == "프롬프트"
            assert max_output_tokens == 123
            return SimpleNamespace(output_text="제목\n---\n본문")

    class FakeOpenAI:
        def __init__(self, api_key: str, timeout: float) -> None:
            assert api_key == "test-key"
            assert timeout == 20.0
            self.responses = FakeResponses()

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    fake_openai = ModuleType("openai")
    fake_openai.OpenAI = FakeOpenAI
    monkeypatch.setitem(sys.modules, "openai", fake_openai)

    assert _call_gpt("프롬프트", max_tokens=123) == {"text": "제목\n---\n본문", "reason": "ok"}


def test_call_gpt_package_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    real_import = builtins.__import__

    def fake_import(name: str, *args, **kwargs):
        if name == "openai":
            raise ImportError("missing openai")
        return real_import(name, *args, **kwargs)

    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.delitem(sys.modules, "openai", raising=False)
    monkeypatch.setattr(builtins, "__import__", fake_import)

    assert _call_gpt("프롬프트") == {"text": None, "reason": "package_missing"}


def test_split_title_body_with_separator() -> None:
    result = _split_title_body("시장 방향성 재점검\n---\n본문입니다.", "기본 제목")

    assert result == {"title": "시장 방향성 재점검", "body": "본문입니다."}


def test_split_title_body_without_separator() -> None:
    result = _split_title_body("시장 방향성 재점검\n본문입니다.", "기본 제목")

    assert result == {"title": "시장 방향성 재점검", "body": "본문입니다."}


@pytest.mark.parametrize(
    ("reason", "message"),
    [
        ("missing_api_key", "AI 칼럼: OPENAI_API_KEY가 설정되지 않았습니다."),
        ("package_missing", "AI 칼럼: openai 패키지가 설치되지 않았습니다."),
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
