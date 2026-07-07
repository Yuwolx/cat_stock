import pytest

from src.utils.ttl_cache import clear_ttl_cache


@pytest.fixture(autouse=True)
def _isolate_ttl_cache():
    clear_ttl_cache()
    yield
    clear_ttl_cache()
