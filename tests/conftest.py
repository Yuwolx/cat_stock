import pytest

from src.utils import report_store
from src.utils.ttl_cache import clear_ttl_cache


@pytest.fixture(autouse=True)
def _isolate_ttl_cache():
    clear_ttl_cache()
    yield
    clear_ttl_cache()


@pytest.fixture(autouse=True)
def _isolate_report_store(tmp_path, monkeypatch):
    monkeypatch.setattr(report_store, "_db_path", lambda: tmp_path / "test_reports.db")
