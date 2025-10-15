from __future__ import annotations

import json
import re
import uuid
from typing import Any

from agent_jupyter_toolkit.notebook import NotebookSession
from agent_jupyter_toolkit.utils.execution import execute_code, invoke_code_cell
from agent_jupyter_toolkit.utils.packages import update_dependencies
from mcp.server import Server
from pydantic import Field

_ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")

# Single shared Postgres client per kernel (stored in kernel globals)
_PG_VAR = "__JAT_PG__"


def register_postgresql_tools(server: Server, session: NotebookSession) -> None:
    """
    Register PostgreSQL data-access tools into an MCP server targeting a live Jupyter kernel.

    Overview
    --------
    - Ensures required dependencies are available inside the kernel.
    - Creates/keeps a single shared `PostgresClient` in the kernel globals.
    - Exposes a visible query→DataFrame tool and hidden schema helpers.

    Environment
    -----------
    The kernel must have one of:
      - PG_DSN
      - POSTGRES_DSN
      - DATABASE_URL

    Tools
    -----
    db.postgresql.query.to_df(raw_sql: str, *, limit: Optional[int] = 50) -> dict
        Creates/uses a shared client, inserts one visible cell that:
          - runs `pg.query_df(sql=_sql, limit=limit)`
          - saves to `df_<short-uuid>`
          - shows a `.head(5)` preview
        Then runs a hidden cell to return:
          - schema ([(name, dtype)])
          - row_count, col_count
          - sample (first 5 rows as JSON)
          - notebook variable name and created cell index

    db.postgresql.schema.list_tables(
        schema_name: Optional[str] = None,
        include_matviews: bool = False
    ) -> dict
        Hidden: returns base tables/views (optionally includes materialized views).

    db.postgresql.schema.list_columns(schema_name: str, table: str) -> dict
        Hidden: returns information_schema column metadata for (schema, table).

    db.postgresql.schema.tree(limit_per_schema: Optional[int] = 100) -> dict
        Hidden: returns a compact [{schema, tables:[...]}] list, limited per schema.
    """

    # -------------------------------------------------------------------------
    # Internals
    # -------------------------------------------------------------------------

    async def _ensure_started() -> None:
        """Start the session if needed."""
        if not await session.is_connected():
            await session.start()

    async def _ensure_deps_once() -> bool:
        """
        Ensure optional dependencies exist inside the notebook kernel.

        We install the package with its PostgreSQL extras so that importing
        `PostgresClient` works, plus pandas/pyarrow are satisfied.
        """
        return await update_dependencies(
            session.kernel,
            [
                "agent-data-toolkit[postgresql]",
            ],
        )

    async def _run_hidden(code: str, *, timeout: float = 60.0) -> dict[str, Any]:
        """
        Execute hidden Python in the kernel that prints exactly one JSON line.

        Args:
            code: The Python code to execute.
            timeout: Max seconds to wait for execution.

        Returns:
            A dict parsed from JSON printed by the cell. If JSON isn't found,
            returns a diagnostic payload with stderr/stdout and outputs attached.
        """
        res = await execute_code(session.kernel, code, timeout=timeout, format_outputs=True)

        if res.status != "ok":
            return {
                "ok": False,
                "error": res.error_message or (res.stderr or "Kernel execution error"),
                "stderr": res.stderr,
                "stdout": res.stdout,
                "outputs": res.text_outputs,
                "status": res.status,
            }

        # Prefer stdout; fall back to captured text outputs or formatted output
        raw = (res.stdout or "").strip()
        if not raw:
            text_out = "\n".join(res.text_outputs) if res.text_outputs else ""
            raw = (text_out or res.formatted_output or "").strip()

        if not raw:
            error_msg = "No JSON output from kernel (empty cell output)."
            return {"ok": False, "error": error_msg, "status": "error"}

        # Remove ANSI sequences that can wrap/contaminate JSON
        raw = _ANSI_RE.sub("", raw)

        # Heuristic: try last JSON-looking line first
        lines = [ln.strip() for ln in raw.splitlines() if ln.strip()]
        for candidate in reversed(lines):
            if candidate.startswith("{") and candidate.endswith("}"):
                try:
                    return json.loads(candidate)
                except Exception:
                    pass

        # Fall back to trying the whole blob
        try:
            return json.loads(raw)
        except Exception:
            error_payload = {
                "ok": False,
                "error": "Malformed JSON from kernel",
                "raw": raw[:4000],
                "status": "error"
            }
            return error_payload

    async def _ensure_pg_client_hidden() -> dict[str, Any]:
        """
        Hidden: validate DSN, init shared client if missing, and ping the DB.

        Returns:
            {"ok": True} on success, otherwise {"ok": False, "error": "..."} with details.
        """
        code = f"""
import os, json
from agent_data_toolkit.postgresql import PostgresClient

PG_VAR = "{_PG_VAR}"
payload = {{"ok": False, "error": None}}

def _dsn():
    return os.getenv("PG_DSN") or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")

try:
    dsn = _dsn()
    if not dsn:
        payload["error"] = "No DSN set (PG_DSN/POSTGRES_DSN/DATABASE_URL)"
        print(json.dumps(payload)); raise SystemExit

    if PG_VAR not in globals():
        try:
            globals()[PG_VAR] = PostgresClient.from_dsn(dsn)
        except Exception as e:
            payload["error"] = f"Failed to init PostgresClient: {{e}}"
            print(json.dumps(payload)); raise SystemExit

    try:
        _ = globals()[PG_VAR].query_rows("SELECT 1 AS ok", limit=1)
    except Exception as e:
        payload["error"] = f"Postgres ping failed: {{e}}"
        print(json.dumps(payload)); raise SystemExit

    payload["ok"] = True
    print(json.dumps(payload))

except SystemExit:
    pass
except Exception as e:
    payload["error"] = str(e)
    print(json.dumps(payload))
"""
        return await _run_hidden(code)

    # -------------------------------------------------------------------------
    # Query → DataFrame tool (1 visible cell, then hidden metadata)
    # -------------------------------------------------------------------------

    async def _create_df_visible_cell(
        raw_sql: str, limit: int | None, df_name: str, preview_rows: int = 5
    ):
        """
        Insert a visible notebook cell that executes a SQL query into a DataFrame and previews it.

        The cell:
          - reads the global Postgres client,
          - assigns the DataFrame to `df_name`,
          - leaves `.head(preview_rows)` as the last expression for rich output.

        Args:
            raw_sql: The raw SQL query to execute.
            limit: Maximum number of rows to fetch (None for no limit).
            df_name: The variable name to assign the DataFrame to.
            preview_rows: Number of rows to show in the cell output preview.

        Returns:
            The result of invoking the code cell, including status and any outputs.
        """
        sql_literal = json.dumps(raw_sql)
        code = f"""
pg = globals().get("{_PG_VAR}")
_sql = {sql_literal}

{df_name} = pg.query_df(sql=_sql, limit={repr(limit)})
{df_name}.head({int(preview_rows)})
"""
        return await invoke_code_cell(session, code)

    async def _extract_df_metadata_hidden(df_name: str) -> dict[str, Any]:
        """
        Hidden: read df_<id> from kernel and emit a JSON payload with schema/counts/sample.

        Args:
            df_name: The variable name of the DataFrame to inspect.

        Returns:
            A dict with keys: ok, error, schema, row_count, col_count, sample
        """
        code = f"""
import json
from datetime import date, datetime
from decimal import Decimal
import uuid
import numpy as _np

name = "{df_name}"
payload = {{
    "ok": False,
    "error": None,
    "schema": None,
    "row_count": None,
    "col_count": None,
    "sample": None
}}

def _json_default(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, (uuid.UUID, Decimal)):
        return str(obj)
    if isinstance(obj, (_np.integer,)):
        return int(obj)
    if isinstance(obj, (_np.floating,)):
        return float(obj)
    if isinstance(obj, (_np.bool_,)):
        return bool(obj)
    if hasattr(obj, "tolist"):
        return obj.tolist()
    return str(obj)

try:
    if name not in globals():
        payload["error"] = f"DataFrame '{{name}}' not found in kernel globals"
        print(json.dumps(payload, default=_json_default)); raise SystemExit

    df = globals()[name]
    payload["schema"] = [(c, str(t)) for c, t in df.dtypes.items()]
    payload["row_count"] = int(df.shape[0])
    payload["col_count"] = int(df.shape[1])

    sample_json = df.head(5).to_json(orient="records", date_format="iso")
    payload["sample"] = json.loads(sample_json)

    payload["ok"] = True
    print(json.dumps(payload, default=_json_default))
except Exception as e:
    payload["error"] = str(e)
    print(json.dumps(payload, default=_json_default))
"""
        return await _run_hidden(code)

    @server.tool(name="db.postgresql.query.to_df")
    async def db_postgresql_query_to_df(
        raw_sql: str = Field(description="The raw SQL query to execute."),
        *,
        limit: int | None = Field(
            default=50, description="Maximum number of rows to fetch (None for no limit)."
        ),
    ) -> dict[str, Any]:
        """
        Execute `raw_sql` in the kernel via the shared Postgres client, create a DataFrame
        in a visible cell for user preview, and return metadata about that DataFrame.
        """
        await _ensure_started()
        await _ensure_deps_once()

        # Hidden init + ping (retry once after deps)
        bootstrap = await _ensure_pg_client_hidden()
        if not bootstrap.get("ok"):
            await _ensure_deps_once()
            bootstrap = await _ensure_pg_client_hidden()
            if not bootstrap.get("ok"):
                return {
                    "ok": False,
                    "df_name": None,
                    "create_cell_index": None,
                    "schema": None,
                    "row_count": None,
                    "col_count": None,
                    "sample": None,
                    "error": bootstrap.get("error") or "Bootstrap failed",
                    "bootstrap": bootstrap,
                    "status": "error",
                }

        df_name = f"df_{uuid.uuid4().hex[:6]}"

        vis_res = await _create_df_visible_cell(raw_sql, limit, df_name, preview_rows=5)
        if vis_res.status != "ok":
            err = vis_res.error_message or (vis_res.stderr.strip() if vis_res.stderr else None)
            if not err and getattr(vis_res, "text_outputs", None):
                err = "\n".join(vis_res.text_outputs)
            return {
                "ok": False,
                "df_name": df_name,
                "create_cell_index": vis_res.cell_index,
                "schema": None,
                "row_count": None,
                "col_count": None,
                "sample": None,
                "error": err or "Kernel execution error",
                "status": vis_res.status,
                "stderr": vis_res.stderr,
                "stdout": vis_res.stdout,
                "outputs": getattr(vis_res, "text_outputs", None),
                "bootstrap": {"ok": True, "error": None},
            }

        meta = await _extract_df_metadata_hidden(df_name)
        if not meta.get("ok"):
            return {
                "ok": False,
                "df_name": df_name,
                "create_cell_index": vis_res.cell_index,
                "schema": None,
                "row_count": None,
                "col_count": None,
                "sample": None,
                "error": meta.get("error") or "Failed to extract DataFrame metadata",
                "status": "error",
                "bootstrap": {"ok": True, "error": None},
            }

        return {
            "ok": True,
            "df_name": df_name,
            "create_cell_index": vis_res.cell_index,
            "schema": meta.get("schema"),
            "row_count": meta.get("row_count"),
            "col_count": meta.get("col_count"),
            "sample": meta.get("sample"),
            "error": None,
            "status": "ok",
            "bootstrap": {"ok": True, "error": None},
        }

    # -------------------------------------------------------------------------
    # Schema tools (all hidden)
    # -------------------------------------------------------------------------

    @server.tool(name="db.postgresql.schema.list_tables")
    async def db_postgresql_schema_list_tables(
        schema_name: str | None = Field(
            default=None, description="Schema name to filter (None for all schemas)."
        ),
        include_matviews: bool = Field(
            default=False, description="Include materialized views in the result."
        ),
    ) -> dict[str, Any]:
        """Hidden: list base tables/views (and optionally materialized views)."""
        await _ensure_started()
        await _ensure_deps_once()

        bootstrap = await _ensure_pg_client_hidden()
        if not bootstrap.get("ok"):
            await _ensure_deps_once()
            bootstrap = await _ensure_pg_client_hidden()
            if not bootstrap.get("ok"):
                return {
                    "ok": False,
                    "tables": [],
                    "error": bootstrap.get("error") or "Bootstrap failed",
                    "bootstrap": bootstrap,
                }

        schema_expr = "None" if schema_name is None else json.dumps(schema_name)
        include_mv_expr = "True" if include_matviews else "False"

        code = f"""
import json
pg = globals().get("{_PG_VAR}")
payload = {{"ok": False, "tables": [], "error": None}}

try:
    schema = {schema_expr}
    include_matviews = {include_mv_expr}

    if schema:
        sql_tv = '''
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_type IN ('BASE TABLE','VIEW') AND table_schema = %(schema)s
        ORDER BY table_schema, table_name
        '''
        rows = pg.query_rows(sql=sql_tv, params={{"schema": schema}})
    else:
        sql_tv = '''
        SELECT table_schema, table_name, table_type
        FROM information_schema.tables
        WHERE table_type IN ('BASE TABLE','VIEW')
        ORDER BY table_schema, table_name
        '''
        rows = pg.query_rows(sql=sql_tv)

    if include_matviews:
        if schema:
            sql_mv = '''
            SELECT schemaname AS table_schema,
                   matviewname AS table_name,
                   'MATERIALIZED VIEW' AS table_type
            FROM pg_matviews
            WHERE schemaname = %(schema)s
            ORDER BY schemaname, matviewname
            '''
            mrows = pg.query_rows(sql=sql_mv, params={{"schema": schema}})
        else:
            sql_mv = '''
            SELECT schemaname AS table_schema,
                   matviewname AS table_name,
                   'MATERIALIZED VIEW' AS table_type
            FROM pg_matviews
            ORDER BY schemaname, matviewname
            '''
            mrows = pg.query_rows(sql=sql_mv)
        rows.extend(mrows)

    payload["ok"] = True
    payload["tables"] = rows
    print(json.dumps(payload))
except Exception as e:
    payload["error"] = str(e)
    print(json.dumps(payload))
"""
        result = await _run_hidden(code)
        result["bootstrap"] = {"ok": True, "error": None} if bootstrap.get("ok") else bootstrap
        return result

    @server.tool(name="db.postgresql.schema.list_columns")
    async def db_postgresql_schema_list_columns(
        schema_name: str = Field(description="The schema name containing the table."),
        table: str = Field(description="The table name to list columns for."),
    ) -> dict[str, Any]:
        """Hidden: list columns for a given (schema, table)."""
        await _ensure_started()
        await _ensure_deps_once()

        bootstrap = await _ensure_pg_client_hidden()
        if not bootstrap.get("ok"):
            await _ensure_deps_once()
            bootstrap = await _ensure_pg_client_hidden()
            if not bootstrap.get("ok"):
                return {
                    "ok": False,
                    "columns": [],
                    "error": bootstrap.get("error") or "Bootstrap failed",
                    "bootstrap": bootstrap,
                }

        code = f"""
import json
pg = globals().get("{_PG_VAR}")
payload = {{"ok": False, "columns": [], "error": None}}

try:
    schema = {json.dumps(schema_name)}
    table = {json.dumps(table)}
    sql = '''
    SELECT column_name,
           data_type,
           is_nullable,
           column_default,
           ordinal_position
    FROM information_schema.columns
    WHERE table_schema = %(schema)s AND table_name = %(table)s
    ORDER BY ordinal_position
    '''
    rows = pg.query_rows(sql=sql, params={{"schema": schema, "table": table}})
    payload["ok"] = True
    payload["columns"] = rows
    print(json.dumps(payload))
except Exception as e:
    payload["error"] = str(e)
    print(json.dumps(payload))
"""
        result = await _run_hidden(code)
        result["bootstrap"] = {"ok": True, "error": None} if bootstrap.get("ok") else bootstrap
        return result

    @server.tool(name="db.postgresql.schema.tree")
    async def db_postgresql_schema_tree(
        limit_per_schema: int | None = Field(
            default=100, description="Limit number of tables per schema (None for no limit)."
        ),
    ) -> dict[str, Any]:
        """Hidden: compact mapping of schema → tables (limited per schema)."""
        await _ensure_started()
        await _ensure_deps_once()

        bootstrap = await _ensure_pg_client_hidden()
        if not bootstrap.get("ok"):
            await _ensure_deps_once()
            bootstrap = await _ensure_pg_client_hidden()
            if not bootstrap.get("ok"):
                return {
                    "ok": False,
                    "schemas": [],
                    "error": bootstrap.get("error") or "Bootstrap failed",
                    "bootstrap": bootstrap,
                }

        lim_expr = "None" if limit_per_schema is None else str(int(limit_per_schema))

        code = f"""
import json
pg = globals().get("{_PG_VAR}")
payload = {{"ok": False, "schemas": [], "error": None}}

try:
    sql_s = "SELECT schema_name AS name FROM information_schema.schemata ORDER BY schema_name"
    schemas = [r["name"] for r in pg.query_rows(sql=sql_s)]

    system_schemas = {{
        "pg_catalog", "information_schema", "pg_toast", "pg_internal",
        "pglogical", "catalog_history"
    }}
    schemas = [s for s in schemas
               if s not in system_schemas
               and not s.startswith("pg_temp")
               and not s.startswith("pg_toast_temp")]

    limit_per_schema = {lim_expr}
    out = []
    for s in schemas:
        sql_t = '''
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type IN ('BASE TABLE','VIEW') AND table_schema = %(schema)s
        ORDER BY table_name
        '''
        rows = pg.query_rows(sql=sql_t, params={{"schema": s}})
        names = [r["table_name"] for r in rows]
        if isinstance(limit_per_schema, int):
            names = names[:limit_per_schema]
        out.append({{"schema": s, "tables": names}})

    payload["ok"] = True
    payload["schemas"] = out
    print(json.dumps(payload))
except Exception as e:
    payload["error"] = str(e)
    print(json.dumps(payload))
"""
        result = await _run_hidden(code)
        result["bootstrap"] = {"ok": True, "error": None} if bootstrap.get("ok") else bootstrap
        return result

    @server.tool(name="db.postgresql.reset")
    async def db_postgresql_reset() -> dict[str, Any]:
        """Hidden: forcibly re-initialize the shared Postgres client.

        Use this when the DB was restarted and needs to be reconnected.
        """
        await _ensure_started()
        await _ensure_deps_once()
        code = f"""
    import os, json
    from agent_data_toolkit.postgresql import PostgresClient
    PG_VAR = "{_PG_VAR}"
    payload = {{"ok": False, "error": None}}
    try:
        dsn = os.getenv("PG_DSN") or os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
        if not dsn:
            payload["error"] = "No DSN set (PG_DSN/POSTGRES_DSN/DATABASE_URL)"
        else:
            old = globals().pop(PG_VAR, None)
            if old is not None:
                try:
                    old.close()
                except Exception:
                    pass
            globals()[PG_VAR] = PostgresClient.from_dsn(dsn)
            _ = globals()[PG_VAR].query_rows("SELECT 1", limit=1)
            payload["ok"] = True
        print(json.dumps(payload))
    except Exception as e:
        payload["error"] = str(e)
        print(json.dumps(payload))
    """
        return await _run_hidden(code)
