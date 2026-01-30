# KappaLake - Micro Data Lakehouse

KappaLake is a cloud-native, open-source, and containerized data platform acting as a "Micro Data Lakehouse". It democratizes data engineering through AI automation, allowing full lifecycle management (ingestion, curation, governance, and consumption) under a Medallion architecture.

## 🚀 Getting Started

### Prerequisites

*   Docker & Docker Compose (with Docker Desktop running on Windows/Mac)
*   4GB+ RAM recommended (for LLM and services)

### Installation

1.  Clone the repository.
2.  Start the infrastructure:

    ```bash
    docker-compose up -d --build
    ```

3.  Wait for services to initialize (especially the LLM model download on first run).

### Access Points

| Service | URL | Credentials (User/Pass) |
| :--- | :--- | :--- |
| **KappaLake UI** | [http://localhost:3001](http://localhost:3001) | - |
| **Dagster UI** | [http://localhost:3000](http://localhost:3000) | - |
| **Trino UI** | [http://localhost:8080](http://localhost:8080) | `admin` / (empty) |
| **MinIO Console**| [http://localhost:9001](http://localhost:9001) | `minioadmin` / `minioadmin` |
| **Flink Dashboard**| [http://localhost:8081](http://localhost:8081) | - |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs)| - |

## 🏗 Architecture

KappaLake uses a Polylithic architecture with decoupled components:

*   **Ingestion**: PyAirbyte (Embedded in Dagster) & Redpanda (Streaming).
*   **Storage**: MinIO (S3) + Apache Iceberg (Table Format).
*   **Compute**: Trino (Federated SQL) & DuckDB (Local transformations).
*   **Orchestration**: Dagster (Asset-based).
*   **AI Engine**: Local LLM (Qwen2.5-1.5B via llama.cpp) + FastAPI.
*   **Frontend**: Next.js Chat Interface.

## 🧪 Usage Examples

### 1. Ingest Data (Bronze Layer)
1.  Go to **Dagster UI** ([localhost:3000](http://localhost:3000)).
2.  Navigate to `Assets` -> `faker_users_bronze`.
3.  Click **Materialize**.
4.  Dagster will launch a Docker container to run Airbyte's Faker source and ingest 100 fake users into the system (cached in DuckDB for this MVP).

### 2. Chat with Data (AI Copilot)
1.  Go to **KappaLake UI** ([localhost:3001](http://localhost:3001)).
2.  Type a request like:
    > "Show me the top 5 users from the bronze table"
    > "Count the total records in the users table"
3.  The AI will interpret your intent, look at the Trino schema, and generate the SQL query to fetch the results.

## 🛠 Development

### Directory Structure
*   `apps/`: Application code (API, UI).
*   `infra/`: Infrastructure configuration (MinIO, Trino, Dagster, LLM).
*   `docker-compose.yml`: Main orchestration file.

### Troubleshooting

*   **LLM Connection**: If the chat fails, check `docker logs kappalake-llm` to ensure the model has finished downloading.
*   **Dagster Errors**: If assets fail with library errors, try reloading the code location in Dagster UI or restarting the container.
