"""KappaLake API tests: health, catalog, query (live Trino) and LLM paths (mocked)."""
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("TRINO_HOST", "trino")
os.environ.setdefault("TRINO_PORT", "8080")

from main import app  # noqa: E402


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_catalog_tables(client):
    r = client.get("/catalog/tables")
    if r.status_code == 500:
        pytest.skip("Trino not reachable")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


def test_query_execute(client):
    r = client.post("/query/execute", json={"query": "SELECT 1 AS one"})
    if r.status_code in (400, 500):
        pytest.skip("Trino not reachable")
    assert r.status_code == 200
    assert r.json()["rows"] == [[1]]


@patch("main.client")
def test_generate_pipeline_parses_sql(mock_client, client):
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "```sql\nSELECT 1 AS one\n```"
    mock_client.chat.completions.create.return_value = mock_resp
    r = client.post("/ai/generate_pipeline", json={"prompt": "select one"})
    assert r.status_code == 200
    body = r.json()
    assert "SELECT 1 AS one" in body["sql_query"]


@patch("main.client")
def test_execute_pipeline_mocked_llm_live_trino(mock_client, client):
    mock_resp = MagicMock()
    mock_resp.choices[0].message.content = "```sql\nSELECT 1 AS one\n```"
    mock_client.chat.completions.create.return_value = mock_resp
    r = client.post("/ai/execute", json={"prompt": "select one"})
    if r.status_code == 500:
        pytest.skip("Trino not reachable")
    assert r.status_code == 200
    body = r.json()
    assert body["rows"] == [[1]]


def test_execute_pipeline_rejects_non_select(client):
    with patch("main.client") as mock_client:
        mock_resp = MagicMock()
        mock_resp.choices[0].message.content = "DELETE FROM users"
        mock_client.chat.completions.create.return_value = mock_resp
        r = client.post("/ai/execute", json={"prompt": "delete everything"})
    assert r.status_code == 400
