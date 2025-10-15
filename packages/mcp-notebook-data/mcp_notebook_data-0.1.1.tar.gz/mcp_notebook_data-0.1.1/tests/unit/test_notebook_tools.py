from unittest.mock import AsyncMock

import pytest
from agent_jupyter_toolkit.notebook.types import (
    NotebookCodeExecutionResult,
    NotebookMarkdownCellResult,
)

from mcp_notebook_data.tools.notebook import register_notebook_tools


def test_register_notebook_tools_registers_expected_tools(dummy_server, mock_session):
    register_notebook_tools(dummy_server, mock_session)
    expected = {"notebook.markdown.add", "notebook.code.run", "notebook.packages.add"}
    assert expected.issubset(set(dummy_server.tools.keys()))


@pytest.mark.asyncio
async def test_notebook_markdown_add_calls_invoke_markdown_cell(
    monkeypatch, dummy_server, mock_session
):
    mock_result = NotebookMarkdownCellResult(
        status="ok",
        cell_index=42,
        error_message=None,
        elapsed_seconds=0.01,
    )
    monkeypatch.setattr(
        "mcp_notebook_data.tools.notebook.invoke_markdown_cell",
        AsyncMock(return_value=mock_result),
    )

    register_notebook_tools(dummy_server, mock_session)
    tool_fn = dummy_server.tools["notebook.markdown.add"]
    result = await tool_fn("# Hello")
    assert result["ok"] is True
    assert result["index"] == 42
    assert result["error"] is None
    assert result["elapsed_seconds"] == 0.01
    assert result.get("status") == "ok"


@pytest.mark.asyncio
async def test_notebook_code_run_calls_invoke_code_cell(
    monkeypatch, dummy_server, mock_session
):
    mock_result = NotebookCodeExecutionResult(
        status="ok",
        execution_count=1,
        cell_index=5,
        stdout="hi\n",
        stderr="",
        outputs=[],
        text_outputs=["hi"],
        formatted_output="hi",
        error_message=None,
        elapsed_seconds=0.02,
    )
    monkeypatch.setattr(
        "mcp_notebook_data.tools.notebook.invoke_code_cell",
        AsyncMock(return_value=mock_result),
    )

    register_notebook_tools(dummy_server, mock_session)
    tool_fn = dummy_server.tools["notebook.code.run"]
    result = await tool_fn("print('hi')")

    assert result == {
        "ok": True,
        "cell_index": 5,
        "status": "ok",
        "stdout": "hi\n",
        "stderr": "",
        "outputs": [],
        "text_outputs": ["hi"],
        "formatted_output": "hi",
        "error_message": None,
        "elapsed_seconds": 0.02,
    }


@pytest.mark.asyncio
async def test_notebook_packages_add_calls_update_dependencies(
    monkeypatch, dummy_server, mock_session
):
    # We only need to assert we call update_dependencies successfully.
    monkeypatch.setattr(
        "mcp_notebook_data.tools.notebook.update_dependencies",
        AsyncMock(return_value=True),
    )

    register_notebook_tools(dummy_server, mock_session)
    tool_fn = dummy_server.tools["notebook.packages.add"]
    result = await tool_fn(["pandas", "numpy"])
    assert result == {"ok": True, "packages": ["pandas", "numpy"]}
