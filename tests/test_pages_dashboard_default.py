from types import SimpleNamespace

from src.ui import pages


class _FakeExpander:
    def __init__(self, calls: list[tuple], label: str) -> None:
        self._calls = calls
        self._label = label

    def __enter__(self) -> None:
        self._calls.append(("expander_enter", self._label))

    def __exit__(self, exc_type, exc, tb) -> None:
        self._calls.append(("expander_exit", self._label))


def test_stock_output_renders_text_as_primary_result(monkeypatch) -> None:
    calls: list[tuple] = []
    fake_st = SimpleNamespace(
        session_state={"market_result": {"payload": {"ok": True}, "text": "TXT"}},
        html=lambda html: calls.append(("html", html)),
        expander=lambda label: _FakeExpander(calls, label),
    )
    monkeypatch.setattr(pages, "st", fake_st)
    monkeypatch.setattr(
        pages,
        "_render_output_box",
        lambda result_text, placeholder, box_key: calls.append(("output", result_text, box_key)),
    )

    pages._render_dashboard_with_text_output(
        result_key="market_result",
        box_key="market",
        placeholder="placeholder",
    )

    assert calls == [("output", "TXT", "market")]


def test_stock_output_empty_state_keeps_placeholder(monkeypatch) -> None:
    calls: list[tuple] = []
    fake_st = SimpleNamespace(session_state={}, html=lambda html: calls.append(("html", html)))
    monkeypatch.setattr(pages, "st", fake_st)
    monkeypatch.setattr(
        pages,
        "_render_output_box",
        lambda result_text, placeholder, box_key: calls.append(("output", result_text, placeholder, box_key)),
    )

    pages._render_dashboard_with_text_output(
        result_key="market_result",
        box_key="market",
        placeholder="placeholder",
    )

    assert calls == [("output", "", "placeholder", "market")]


def test_newspaper_button_opens_dedicated_view(monkeypatch) -> None:
    calls: list[tuple] = []
    fake_st = SimpleNamespace(
        session_state={},
        button=lambda label, **kwargs: calls.append(("button", label, kwargs.get("key"))) or True,
        rerun=lambda: calls.append(("rerun",)),
    )
    monkeypatch.setattr(pages, "st", fake_st)

    pages._render_newspaper_button(
        title="시황 브리핑 신문",
        html="<html>paper</html>",
        file_name="market.html",
        key="market_newspaper_view",
    )

    assert fake_st.session_state["newspaper_view"] == {
        "title": "시황 브리핑 신문",
        "html": "<html>paper</html>",
        "file_name": "market.html",
    }
    assert calls == [("button", "오늘의 신문", "market_newspaper_view"), ("rerun",)]
