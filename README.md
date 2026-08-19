# KappaLake - Micro Data Lakehouse

KappaLake is a cloud-native, open-source, and containerized data platform acting as a "Micro Data Lakehouse". It democratizes data engineering through AI automation, allowing full lifecycle management (ingestion, curation, governance, and consumption) under a **Medallion architecture** (Bronze / Silver / Gold) on **Apache Iceberg**.

## 🚀 Getting Started

### Prerequisites

*   Docker & Docker Compose (with Docker Desktop running on Windows/Mac)
*   8GB+ RAM recommended (LLM, Trino, Keycloak, streaming)

### Installation

```bash
git clone https://github.com/aitups/kappalake.git
cd kappalake

docker compose up -d --build
```

> **Note (private dependency):** the agentic layer uses `aitups/fastpath`
> (a private repo). `docker-compose.yml` mounts it from `../fastpath` and adds it
> to the API's `PYTHONPATH`. Make sure a checkout exists at `../fastpath` (next
> to this repo) and is up to date:
> `git -C ../fastpath pull origin main`. Once fastpath is public, replace the
> mount with `fastpath @ git+https://github.com/aitups/fastpath.git@main` in
> `apps/api/requirements.txt`.

Wait for the services to initialize. On the first run Hayai preloads the default
model (SmolLM2-135M-Instruct) into memory.

### Access Points

| Service | URL | Credentials (User/Pass) |
| :--- | :--- | :--- |
| **KappaLake UI** | http://localhost:3001 | - |
| **Dagster UI** | http://localhost:3000 | - |
| **Trino UI** | http://localhost:8080 | `admin` / (empty) |
| **MinIO Console** | http://localhost:9001 | `minioadmin` / `minioadmin` |
| **Flink Dashboard** | http://localhost:8081 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **LLM (Hayai)** | http://localhost:8085/v1/models | - |
| **Keycloak** | http://localhost:8180 | `admin` / `admin` |
| **Redpanda** | http://localhost:8082 | - |

## 🏗 Architecture

KappaLake uses a Polylithic architecture with decoupled components:

*   **Ingestion**: PyAirbyte (Dagster) for batch + Redpanda for streaming.
*   **Storage**: MinIO (S3) + Apache Iceberg (Table Format), written natively via PyIceberg.
*   **Compute**: Trino (Federated SQL) & DuckDB (local cache).
*   **Orchestration**: Dagster (Asset-based Medallion pipeline).
*   **AI Engine**: Hayai (OpenAI-compatible weight-streaming LLM server).
*   **Agentic layer**: FastPath orchestrator (AI data engineer with Trino tools).
*   **Frontend**: Next.js Chat Interface (Copilot + Agent modes).
*   **Security**: Keycloak (OIDC) - optional JWT verification for the API.

### Medallion pipeline

Dagster materializes three assets into the Iceberg catalog on MinIO:

1.  `bronze_users` - PyAirbyte `source-faker` writes raw rows via PyIceberg.
2.  `silver_users` - Trino `CREATE OR REPLACE TABLE ... AS SELECT` (typed + cleaned).
3.  `gold_user_stats` - Trino aggregation (nationality, languages, avg age).

Streaming events (`stream-producer` -> Redpanda topic `users` ->
`stream-consumer`) land in `bronze.users_stream`.

## 🧪 Usage Examples

### 1. Ingest data (Bronze/Silver/Gold)

1.  Open Dagster (http://localhost:3000).
2.  Go to `Assets` -> materialize `bronze_users`, `silver_users`, `gold_user_stats`.
3.  Query the layers from Trino: `SELECT * FROM iceberg.gold.user_stats;`

### 2. Chat with data (AI Copilot)

1.  Open KappaLake UI (http://localhost:3001).
2.  Copilot mode: type "Show the top 5 nationalities by users". The LLM
    generates a Trino query, executes it, and renders the results table.
3.  Agent mode: type "Create a gold table with users per nationality". The
    FastPath agent inspects the schema and creates the curated table.

## 🤖 LLM / Hayai notes

*   The LLM service runs `aitups/hayai` (OpenAI-compatible). The model is
    selected by its GGUF file name via `LLM_MODEL` (default
    `SmolLM2-135M-Instruct-Q4_K_M`).
*   Models live in `infra/llm/models/` and are auto-scanned at startup.
*   **Known upstream issue:** Hayai's engine currently produces incorrect logits
    for Qwen2.5/Qwen3 GGUFs (they are architecturally recognized but output
    garbage). The GGUF files are kept in `infra/llm/models/` for when this is
    fixed upstream. Until then, use a model from Hayai's tested families
    (SmolLM2 etc.) or set `LLM_MODEL` to a working model.
*   A tokenizer fix (GPT-2 byte-level BPE `bytes_to_unicode`) was contributed
    upstream to `aitups/hayai`; rebuild the image locally
    (`cd ../hayai && docker build -t aitups/hayai:latest .`) to pick it up.
*   Context window, memory strategy and device are configurable via `HAYAI_*`
    env vars in `docker-compose.yml`.

## 🔐 Security

*   Keycloak starts with the `kappalake` realm (clients `kappalake-ui` and
    `kappalake-api`; demo user `demo` / `demo1234`).
*   UI login: http://localhost:3001/login (OIDC authorization code flow).
*   API JWT verification is opt-in: set `AUTH_ENABLED=true` in the `api`
    service to protect `/catalog/*` and `/query/*` with Keycloak JWTs.

## 🛠 Development

### Directory Structure
*   `apps/`: Application code (API, UI).
*   `infra/`: Infrastructure (MinIO, Trino, Dagster, Keycloak, Flink/streaming, LLM).
*   `scripts/`: Smoke tests and helpers.
*   `docker-compose.yml`: Main orchestration file.
*   `kappalake.org/`: **Not part of this repository** - it is the private website
    repo (`aitups/kappalake-web`), kept as an independent working copy and fully
    ignored by git.

### Tests

```bash
# API tests (run inside the api image)
docker compose run --rm --entrypoint python api -m pytest tests -q

# End-to-end smoke test (needs the stack up)
powershell -File scripts/smoke_test.ps1
```

### Troubleshooting

*   **LLM Connection**: if the chat fails, check `docker logs kappalake-llm`
    (Hayai serves models on :8085).
*   **Dagster Errors**: if assets fail with library errors, try reloading the
    code location in Dagster UI or restarting the container.
*   **Port conflicts**: the UI uses host port 3001; if taken by another service,
    change the `ui` port mapping in `docker-compose.yml`.
*   **io_uring**: Docker's default seccomp blocks it; Hayai falls back to
    buffered file I/O automatically.
