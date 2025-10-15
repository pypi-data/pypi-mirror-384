from unittest.mock import AsyncMock, MagicMock

import pytest


class DummyServer:
    """Capture tools registered via @server.tool(name=...)."""
    def __init__(self):
        self.tools = {}

    def tool(self, name=None, **_):
        def decorator(fn):
            self.tools[name] = fn
            return fn
        return decorator


@pytest.fixture
def dummy_server():
    return DummyServer()


@pytest.fixture
def mock_session():
    """
    Mock NotebookSession with async methods used by the tools.
    We patch invoke_* functions directly in tests, so this can stay light.
    """
    session = MagicMock()
    session.is_connected = AsyncMock(return_value=True)
    session.start = AsyncMock()
    session.kernel = MagicMock()
    session.kernel.is_alive = AsyncMock(return_value=True)
    return session
