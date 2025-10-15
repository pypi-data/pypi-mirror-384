# Quickstart: PostgreSQL + Jupyter (MCP Notebook Data)

Run a local PostgreSQL in Docker, then drive a remote (or local) Jupyter notebook through your MCP server (mcp-notebook-data).
An agent will add markdown, execute code cells, inspect schema via Postgres tools, and load a small sample into a DataFrame.

## 1) Configure environment

Create your .env:

```bash
cp .env.example .env
```

Edit values as needed (see .env.example at the bottom). The important bits are:

* Postgres
    * container auth + DB name
    * `PG_DSN` used inside the notebook kernel by the Postgres MCP tools
* Jupyter
    * Remote server URL + token (or switch to local mode in the notebook)
* Azure OpenAI
    * Keys for the agent if you use dapr_agents + AOAI (as in the example notebook)

## 2) Start PostgreSQL

From this folder:

```bash
docker compose up
```

## 3) Python environment

### Using uv (recommended)

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Using pip

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The MCP Postgres tool ensures kernel-side packages as needed (psycopg, pandas, pyarrow), so you don’t have to install them on the host.

## 4) Run the notebook

Open and run:

```
notebooks/01_mcp_postgres_agent.ipynb
```

What it does:

1. Loads .env
2. Launches mcp-notebook-data over stdio
3. Connects to the remote Jupyter (or local if you flip the mode in the notebook)
4. Discovers notebook + postgresql tools
5. Asks the agent to:
    * enumerate schemas/tables
    * choose a table
    * query a small sample into a DataFrame
    * create simple plots
    * add short markdown explanations and a summary