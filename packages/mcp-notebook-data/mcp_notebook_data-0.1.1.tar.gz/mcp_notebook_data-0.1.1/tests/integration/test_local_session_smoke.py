import os

import pytest
from agent_jupyter_toolkit.notebook import NotebookSession
from agent_jupyter_toolkit.utils import create_kernel, create_notebook_transport

pytestmark = pytest.mark.integration


def _skip_if_not_enabled():
    if os.getenv("RUN_INTEGRATION") != "1":
        pytest.skip("Set RUN_INTEGRATION=1 to run integration tests")


@pytest.mark.asyncio
async def test_run_simple_code_cell_locally(tmp_path):
    _skip_if_not_enabled()

    # Build a true local session (no server transport)
    kernel = create_kernel("local", kernel_name="python3")
    nb_path = tmp_path / "smoke.ipynb"
    doc = create_notebook_transport(
        "local",
        str(nb_path),
        prefer_collab=False,
        create_if_missing=True,
    )
    session = NotebookSession(kernel=kernel, doc=doc)

    try:
        await session.start()
        # Execute a trivial cell using the same util your tools call
        from agent_jupyter_toolkit.utils.execution import invoke_code_cell
        res = await invoke_code_cell(session, "x = 2 + 2\nx")
        assert res.status == "ok"
        # res.text_outputs contains the pretty-printed last expression (x)
        assert "4" in (res.formatted_output or "") or "4" in "".join(res.text_outputs or [])
    finally:
        await session.stop()
