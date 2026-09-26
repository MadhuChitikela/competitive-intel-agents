import pytest
from app.mcp_server import _SIGNALS_SEEN, _NEWS_STORE, _PRICING_STORE, _JOBS_STORE


@pytest.fixture(autouse=True)
def reset_in_memory_stores():
    """Reset MCP server in-memory state before each test."""
    _SIGNALS_SEEN.clear()
    _NEWS_STORE.clear()
    _PRICING_STORE.clear()
    _JOBS_STORE.clear()
    yield
    _SIGNALS_SEEN.clear()
    _NEWS_STORE.clear()
    _PRICING_STORE.clear()
    _JOBS_STORE.clear()
