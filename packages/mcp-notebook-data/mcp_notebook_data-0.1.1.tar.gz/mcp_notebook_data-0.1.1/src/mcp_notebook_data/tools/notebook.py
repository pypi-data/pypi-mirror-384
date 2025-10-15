from __future__ import annotations

from typing import Any

from agent_jupyter_toolkit.notebook import NotebookSession
from agent_jupyter_toolkit.utils.execution import (
    invoke_code_cell,
    invoke_markdown_cell,
)
from agent_jupyter_toolkit.utils.packages import update_dependencies
from mcp.server import Server
from pydantic import Field

# Default execution timeout (seconds) for code cells
_DEFAULT_CODE_TIMEOUT_S = 60.0


def register_notebook_tools(server: Server, session: NotebookSession) -> None:
    """
    Register generic Notebook tools for an MCP server targeting a live Jupyter kernel.

    Tools
    -----
    notebook.markdown.add(content: str) -> dict
        Append a markdown cell to the current notebook and return its index and status.

    notebook.code.run(content: str, *, timeout: float = 60.0) -> dict
        Append a code cell, execute it, and return status + rich outputs.

    notebook.packages.add(packages: list[str]) -> dict
        Ensure the given Python packages are available inside the kernel (best-effort).
    """

    async def _ensure_started() -> None:
        """Start the session if needed (idempotent)."""
        if not await session.is_connected():
            await session.start()

    @server.tool(name="notebook.markdown.add")
    async def notebook_markdown_add(
        content: str = Field(
            description="The markdown content to insert into a new cell."
        ),
    ) -> dict[str, Any]:
        """
        Append a markdown cell and return its result.
        """
        await _ensure_started()
        result = await invoke_markdown_cell(session, content)
        return {
            "ok": result.status == "ok",
            "index": result.cell_index,
            "status": result.status,
            "error": result.error_message,
            "elapsed_seconds": result.elapsed_seconds,
        }

    @server.tool(name="notebook.code.run")
    async def notebook_code_run(
        content: str = Field(
            description="The Python code to insert and execute in a new cell."
        ),
        *,
        timeout: float = Field(
            default=_DEFAULT_CODE_TIMEOUT_S,
            description="Maximum time (in seconds) to allow the cell execution to run.",
            ge=1.0,
        ),
    ) -> dict[str, Any]:
        """
        Append a code cell, execute it, and return rich outputs.
        """
        await _ensure_started()
        result = await invoke_code_cell(session, content, timeout=timeout)
        return {
            "ok": result.status == "ok",
            "cell_index": result.cell_index,
            "status": result.status,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "outputs": result.outputs,
            "text_outputs": result.text_outputs,
            "formatted_output": result.formatted_output,
            "error_message": result.error_message,
            "elapsed_seconds": result.elapsed_seconds,
        }

    @server.tool(name="notebook.packages.add")
    async def notebook_packages_add(
        packages: list[str] = Field(  # noqa: B008
            description="Python package specifiers to install/ensure inside the kernel.",
        ),
    ) -> dict[str, Any]:
        """
        Ensure the given packages are available in the kernel (best-effort).
        - Preserves the input order.
        - Dedupe while keeping the first occurrence.
        """
        await _ensure_started()

        # Normalize input (strip, drop non-str/empty)
        cleaned = [p.strip() for p in (packages or []) if isinstance(p, str) and p.strip()]
        # Dedupe but preserve order
        ordered = list(dict.fromkeys(cleaned))

        if not ordered:
            return {"ok": True, "packages": [], "note": "No packages provided."}

        try:
            ok = await update_dependencies(session.kernel, ordered)
            return {"ok": bool(ok), "packages": ordered}
        except Exception as e:
            # Surface a concise error without crashing the tool
            return {"ok": False, "packages": ordered, "error": str(e)}
