from mcp_notebook_data.server import _parse_headers_env


def test_parse_headers_env_valid(monkeypatch):
    monkeypatch.setenv(
        "MCP_JUPYTER_HEADERS_JSON",
        '{"Authorization": "Bearer token", "X-Test": "yes"}'
    )
    headers = _parse_headers_env()
    assert headers == {"Authorization": "Bearer token", "X-Test": "yes"}


def test_parse_headers_env_invalid_json(monkeypatch):
    monkeypatch.setenv("MCP_JUPYTER_HEADERS_JSON", "{bad json}")
    headers = _parse_headers_env()
    assert headers == {}


def test_parse_headers_env_not_dict(monkeypatch):
    monkeypatch.setenv("MCP_JUPYTER_HEADERS_JSON", "[1,2,3]")
    headers = _parse_headers_env()
    assert headers == {}


def test_parse_headers_env_missing(monkeypatch):
    monkeypatch.delenv("MCP_JUPYTER_HEADERS_JSON", raising=False)
    headers = _parse_headers_env()
    assert headers == {}
