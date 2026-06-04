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


def test_stock_output_renders_dashboard_before_text_expander(monkeypatch) -> None:
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
        dashboard_builder=lambda payload: "DASHBOARD",
    )

    assert calls == [
        ("html", "DASHBOARD"),
        ("expander_enter", "텍스트로 보기/복사"),
        ("output", "TXT", "market"),
        ("expander_exit", "텍스트로 보기/복사"),
    ]


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
        dashboard_builder=lambda payload: "DASHBOARD",
    )

    assert calls == [("output", "", "placeholder", "market")]
