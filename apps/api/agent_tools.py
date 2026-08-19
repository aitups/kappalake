"""FastPath tools backed by the KappaLake Trino/Iceberg lakehouse."""
import os

import trino
from fastpath.tools import Tool

TRINO_HOST = os.getenv("TRINO_HOST", "trino")
TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))
TRINO_USER = os.getenv("TRINO_USER", "admin")


def _conn():
    return trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog="iceberg",
        schema="default",
        http_scheme="http",
    )


def _exec(sql: str):
    conn = _conn()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        cols = [d[0] for d in cur.description] if cur.description else []
        rows = cur.fetchall() if cur.description else []
        conn.commit()
        return cols, rows
    finally:
        cur.close()
        conn.close()


def _fmt(cols, rows, limit: int = 25):
    lines = []
    for r in rows[:limit]:
        lines.append(", ".join(f"{c}={v}" for c, v in zip(cols, r)))
    return "\n".join(lines) if lines else "(no rows)"


class ListTablesTool(Tool):
    def __init__(self):
        super().__init__(
            name="list_tables",
            description="List the tables in the KappaLake data lake (Iceberg catalog) as schema.table.",
        )

    def run(self, text="", **kwargs):
        cols, rows = _exec(
            "SELECT table_schema, table_name FROM information_schema.tables "
            "WHERE table_schema NOT IN ('information_schema', 'default') ORDER BY 1, 2"
        )
        return "\n".join(f"- {s}.{t}" for s, t in rows) or "(no tables found)"


class DescribeTableTool(Tool):
    def __init__(self):
        super().__init__(
            name="describe_table",
            description="Describe the columns of a table. Pass the table name like 'silver.users'.",
        )

    def run(self, text, **kwargs):
        name = (text or "").strip().strip('"')
        if not name:
            return "Provide a table name, e.g. silver.users"
        if "." not in name:
            name = f"default.{name}"
        try:
            cols, rows = _exec(f"DESCRIBE iceberg.{name}")
        except Exception as e:
            return f"Error describing {name}: {e}"
        return "\n".join(f"- {r[0]} {r[1]}" for r in rows[:60])


class ExecuteQueryTool(Tool):
    def __init__(self):
        super().__init__(
            name="execute_query",
            description="Execute a read-only SQL query (SELECT/WITH/SHOW/DESCRIBE) against the lakehouse and return the rows.",
        )

    def run(self, text, **kwargs):
        sql = (text or "").strip()
        if not sql:
            return "No SQL provided."
        if not sql.upper().lstrip().startswith(("SELECT", "WITH", "SHOW", "DESCRIBE")):
            return "Only read-only queries are allowed (SELECT/WITH/SHOW/DESCRIBE)."
        try:
            cols, rows = _exec(sql)
        except Exception as e:
            return f"Query error: {e}"
        return f"Columns: {', '.join(cols)}\n" + _fmt(cols, rows)


class CreateGoldTableTool(Tool):
    def __init__(self):
        super().__init__(
            name="create_gold_table",
            description=(
                "Create or replace a gold table from a SELECT. "
                "Pass a statement like: gold.users_by_nationality AS SELECT nationality, COUNT(*) AS n FROM silver.users GROUP BY nationality"
            ),
        )

    def run(self, text, **kwargs):
        spec = (text or "").strip()
        if " as select " not in spec.lower():
            return "Use the format: gold.<name> AS SELECT ... FROM <table>"
        target, sel = spec.split(" as ", 1)
        target = target.strip().strip('"')
        sel = sel.strip()
        if not target.startswith("gold."):
            target = f"gold.{target}"
        try:
            _exec("CREATE SCHEMA IF NOT EXISTS iceberg.gold")
            _exec(f"CREATE OR REPLACE TABLE iceberg.{target} AS {sel}")
        except Exception as e:
            return f"Error creating gold table: {e}"
        _, rows = _exec(f"SELECT count(*) FROM iceberg.{target}")
        return f"Created/replaced gold table {target} with {rows[0][0]} rows."
