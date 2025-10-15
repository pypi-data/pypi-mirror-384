# MCP Notebook Data

An MCP server that lets AI agents run a live Jupyter notebook session creating code and markdown cells, managing Python packages, and connecting to data sources. Unlike MCP servers that fetch data and hand it directly to a language model, `MCP Notebook Data` loads query results into the notebook as pandas DataFrames, so agents analyze with code, explain in markdown, and visualize patterns—all within a single notebook session.

---

## Why

Typical `data MCP servers` fetch data on the server side and pass results straight to an LLM. That clashes with:

* Large datasets (pressure on attention and context-window budgets).
* Data analysis as code (you want imports, transforms, plots, tests).
* Reproducibility (keep reasoning and analysis steps that can be re-run and audited).

> This project flips that model: use the MCP session to operate a Jupyter notebook and materialize data as pandas DataFrames inside the kernel. The agent continues in Python—explore, transform, visualize—without dumping big payloads into prompts.

---

## Core ideas

* **One live notebook session** per MCP server instance (kernel + document).
* **Notebook tools**: add markdown, run code, ensure packages.
* **Data connector tools**: initialize a client inside the kernel, run queries there, and assign `df_<id>` for continued work in Python.
* **Data stays in the kernel**: the server returns only compact JSON metadata (e.g., schema, small sample) to guide the agent.

---

## Tool Included

### Notebook tools (always enabled)

* `notebook.markdown.add(content)`: Append a markdown cell. Returns index, status, timing.
* `notebook.code.run(content)`: Append a Python code cell and execute it. Returns stdout, stderr, rich outputs, status.
* `notebook.packages.add([packages])`: Best-effort ensure pip packages inside the kernel (idempotent).

### Data connector toolsets (opt-in)

#### PostgreSQL tools

* `db.postgresql.schema.list_tables(schema_name=None, include_matviews=False)`: Tables/views (and materialized views if requested).
* `db.postgresql.schema.list_columns(schema_name, table)`: Column metadata for a table.
* `db.postgresql.schema.tree(limit_per_schema=100)`: Compact schema → tables mapping (filters system schemas).
* `db.postgresql.query.to_df(raw_sql, limit=50)`: Executes SQL in the notebook kernel, assigns a DataFrame like `df_ab12cd`, shows a short preview in the notebook, and returns JSON metadata (schema, row/col counts, data sample). A single shared client (`__JAT_PG__`) is reused per kernel.

> Connector drivers (e.g., psycopg) are installed into the notebook kernel on demand, not in the MCP server process.

---

## Installation

### From PyPI

The easiest way is to install the package directly from PyPI:

```bash
# With uv (recommended)
uv pip install mcp-notebook-data

# Or with pip
pip install mcp-notebook-data
```

To enable a specific connector, install with extras. For example, PostgreSQL:

```bash
uv pip install "mcp-notebook-data[postgresql]"
# or
pip install "mcp-notebook-data[postgresql]"
```

### From Source

If you want to work with the latest code from GitHub:

```bash
git clone https://github.com/Cyb3rWard0g/mcp-notebook-data.git
cd mcp-notebook-data

# Create a virtual environment
uv venv .venv
source .venv/bin/activate

# Install in editable/dev mode
uv pip install -e ".[dev]"
# or
pip install -e ".[dev]"
```

You can still add extras here, e.g.:

```bash
uv pip install -e ".[dev,postgresql]"
```

---

## Configure Server

Set environment to point at your Jupyter and (optionally) enable data toolsets:

```bash
# Jupyter (server mode)
export MCP_JUPYTER_SESSION_MODE=server             # or "local"
export MCP_JUPYTER_BASE_URL=http://localhost:8888  # required in server mode
export MCP_JUPYTER_TOKEN=<your-jupyter-token>      # required in server mode
export MCP_JUPYTER_KERNEL_NAME=python3             # default
export MCP_JUPYTER_NOTEBOOK_PATH=mcp_demo.ipynb    # optional; auto name if unset

# Toolsets (comma-separated; notebook is always on)
export MCP_JUPYTER_TOOLSETS=postgresql             # enable Postgres tools

# For Postgres toolset (read by the notebook kernel)
export PG_DSN=postgresql://user:pass@host:5432/db?sslmode=disable
# or POSTGRES_DSN / DATABASE_URL
```

## Run Server

### Stdio (recommended for desktop MCP clients):

```bash
mcp-notebook-data --transport stdio
```

### SSE:

```bash
mcp-notebook-data --transport sse --host 0.0.0.0 --port 8000
```

### Streamable HTTP:

```bash
mcp-notebook-data --transport streamable-http --host 0.0.0.0 --port 8000
```

### With uvx:

```bash
uvx mcp-notebook-data --transport stdio
```

Example client config (stdio)

```json
{
  "mcpServers": {
    "notebook-data": {
      "command": "uvx",
      "args": ["mcp-notebook-data", "--transport", "stdio"],
      "env": {
        "MCP_JUPYTER_SESSION_MODE": "server",
        "MCP_JUPYTER_BASE_URL": "http://localhost:8888",
        "MCP_JUPYTER_TOKEN": "<your-token>",
        "MCP_JUPYTER_KERNEL_NAME": "python3",
        "MCP_JUPYTER_NOTEBOOK_PATH": "mcp_session.ipynb",
        "MCP_JUPYTER_TOOLSETS": "postgresql"
      }
    }
  }
}
```

---

## Quickstarts

### PostgreSQL Data Tools

See [quickstarts/postgresql/](quickstarts/postgresql/README.md) for a self-contained example that:

* spins up Postgres with sample data (docker compose),
* launches the MCP server with the Postgres toolset,
* drives the notebook through an agent using these tools.

## Release Process

To publish a new release to PyPI:

0. Install dev dependencies
    ```sh
    uv pip install -e ".[dev]"
    ``` 
1. Ensure all changes are committed and tests pass:
    ```sh
    uv run pytest tests/
    ```
2. Create and push an **annotated tag** for the release:
    ```sh
    git tag -a v0.1.0 -m "Release 0.1.0"
    git push origin v0.1.0
    ```
3. Checkout the tag to ensure you are building exactly from it:
    ```sh
    git checkout v0.1.0
    ```
4. Clean old build artifacts:
    ```sh
    rm -rf dist
    rm -rf build
    rm -rf src/*.egg-info
    ```
5. Upgrade build and upload tools:
    ```sh
    uv pip install --upgrade build twine packaging setuptools wheel setuptools_scm
    ```
6. Build the package:
    ```sh
    uv run python -m build
    ```
7. (Optional) Check metadata:
    ```sh
    uv run twine check dist/*
    ```
8. Upload to PyPI:
    ```sh
    uv run twine upload dist/*
    ```

**Notes:**
* Twine ≥ 6 and packaging ≥ 24.2 are required for modern metadata support.
* Always build from the tag (`git checkout vX.Y.Z`) so setuptools_scm resolves the exact version.
* `git checkout v0.1.0` puts you in detached HEAD mode; that’s normal. When done, return to your branch with:
    ```sh
    git switch -
    ```
* If you’re building in CI, make sure tags are fetched:
    ```sh
    git fetch --tags --force --prune
    git fetch --unshallow || true
    ```

---

## Running Tests

```bash
uv venv .venv
source .venv/bin/activate

# install your package in editable mode with dev tools
uv pip install -e ".[dev]"

# ruff: lint + fix
ruff check src tests --fix

# black: format
black src tests
```