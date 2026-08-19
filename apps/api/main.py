"""KappaLake API Gateway - schema catalog, SQL execution, AI copilot and FastPath agent."""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import os
from trino.auth import BasicAuthentication
from trino.dbapi import connect

from agent_service import run_agent_task
from auth import get_current_user
from models import (
    AgentRequest,
    AgentResponse,
    Column,
    ExecuteRequest,
    ExecuteResponse,
    PipelineRequest,
    PipelineResponse,
    QueryRequest,
    Table,
)

app = FastAPI(title="KappaLake API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
TRINO_HOST = os.getenv("TRINO_HOST", "trino")
TRINO_PORT = int(os.getenv("TRINO_PORT", 8080))
TRINO_USER = os.getenv("TRINO_USER", "admin")

# LLM Configuration (Local via Hayai - OpenAI-compatible server)
LLM_API_URL = os.getenv("LLM_API_URL", "http://llm:8080/v1")
LLM_API_KEY = "sk-no-key-required"
MODEL_NAME = os.getenv("LLM_MODEL", "SmolLM2-135M-Instruct-Q4_K_M")

client = OpenAI(base_url=LLM_API_URL, api_key=LLM_API_KEY)


def get_trino_connection():
    return connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user=TRINO_USER,
        catalog="iceberg",
        schema="default",
    )


def get_schema_context():
    """Retrieves a simplified schema representation for the LLM context."""
    conn = get_trino_connection()
    cur = conn.cursor()
    try:
        cur.execute("SHOW TABLES FROM iceberg.default")
        tables = [row[0] for row in cur.fetchall()]
        schema_text = "Database Schema:\n"
        for table in tables:
            cur.execute(f"DESCRIBE iceberg.default.{table}")
            columns = [f"{row[0]} ({row[1]})" for row in cur.fetchall()]
            schema_text += f"- Table '{table}': {', '.join(columns)}\n"
        # Include bronze/silver/gold schemas too
        cur.execute("SELECT table_schema, table_name FROM information_schema.tables WHERE table_schema NOT IN ('information_schema', 'default')")
        for t_schema, t_name in cur.fetchall():
            cur.execute(f"DESCRIBE iceberg.{t_schema}.{t_name}")
            columns = [f"{row[0]} ({row[1]})" for row in cur.fetchall()]
            schema_text += f"- Table '{t_schema}.{t_name}': {', '.join(columns)}\n"
        return schema_text
    except Exception:
        return "No tables found in schema."
    finally:
        cur.close()
        conn.close()


@app.get("/")
def read_root():
    return {"message": "Welcome to KappaLake API"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/catalog/tables", response_model=list[Table])
def list_tables(schema: str = "default", user: dict = Depends(get_current_user)):
    """List tables in a specific schema using Trino information_schema."""
    conn = get_trino_connection()
    cur = conn.cursor()
    try:
        query = f"""
            SELECT table_catalog, table_schema, table_name
            FROM information_schema.tables
            WHERE table_schema = '{schema}'
        """
        cur.execute(query)
        tables_data = cur.fetchall()
        results = []
        for t_cat, t_schema, t_name in tables_data:
            col_query = f"""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = '{t_schema}' AND table_name = '{t_name}'
            """
            cur.execute(col_query)
            cols = [Column(name=c[0], type=c[1]) for c in cur.fetchall()]
            results.append(Table(
                catalog=t_cat, schema_name=t_schema, table_name=t_name, columns=cols
            ))
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/query/execute")
def execute_query(request: QueryRequest, user: dict = Depends(get_current_user)):
    """Execute a raw SQL query (Use with caution - for internal/admin use)."""
    conn = get_trino_connection()
    cur = conn.cursor()
    try:
        cur.execute(request.query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        return {"columns": columns, "rows": rows}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()


def _generate_sql(prompt: str):
    """Asks the LLM for a Trino SQL query and returns (sql_query, explanation)."""
    schema_context = get_schema_context()
    system_prompt = f"""You are an expert Data Engineer specializing in Trino SQL.

Your task is to translate the user's natural language request into a valid Trino SQL query.

Context (Available Tables):
{schema_context}

Instructions:
1. Output valid SQL code inside a markdown block (```sql ... ```).
2. Provide a brief explanation outside the code block.
3. Use ONLY the tables/columns listed in the context.
4. If the request requires tables not in the context, say "I cannot fulfill this request because the data is missing."
"""
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )
    content = completion.choices[0].message.content or ""

    sql_query = ""
    if "```sql" in content:
        sql_query = content.split("```sql")[1].split("```")[0].strip()
    elif "SELECT" in content.upper():
        lines = content.split("\n")
        sql_lines = [line for line in lines if line.strip().upper().startswith(("SELECT", "WITH", "CREATE"))]
        if sql_lines:
            sql_query = "\n".join(sql_lines)
    return sql_query, content


@app.post("/ai/generate_pipeline", response_model=PipelineResponse)
def generate_pipeline(request: PipelineRequest):
    """Generates a SQL query based on natural language prompt and schema context."""
    try:
        sql_query, explanation = _generate_sql(request.prompt)
        return PipelineResponse(sql_query=sql_query, explanation=explanation)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/execute", response_model=ExecuteResponse)
def execute_pipeline(request: ExecuteRequest):
    """Generates a SQL query from natural language, executes it and returns the results."""
    try:
        sql_query, explanation = _generate_sql(request.prompt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    if not sql_query or not sql_query.upper().lstrip().startswith(("SELECT", "WITH")):
        raise HTTPException(status_code=400, detail="The LLM did not produce a read-only SQL query.")

    conn = get_trino_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql_query)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        return ExecuteResponse(
            sql_query=sql_query,
            explanation=explanation,
            columns=columns,
            rows=[list(r) for r in rows[:200]],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        cur.close()
        conn.close()


@app.post("/agent/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """Runs an autonomous data-engineering task through the FastPath orchestrator."""
    try:
        result = await run_agent_task(request.task)
        return AgentResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
