FROM python:3.11-slim

ENV DAGSTER_HOME=/opt/dagster/dagster_home

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libpq-dev \
    gcc \
    docker.io \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

# Python dependencies
# dagster-postgres: storage, dagster-docker: docker ops
# airbyte (PyAirbyte): source-faker ingestion
# pyarrow + s3fs: parquet staging to MinIO
# trino: Iceberg DDL / add_files / CTAS
RUN pip install --no-cache-dir \
    dagster \
    dagster-webserver \
    dagster-postgres \
    dagster-docker \
    airbyte \
    pandas \
    pyarrow \
    s3fs \
    trino \
    psycopg2-binary \
    duckdb \
    pyiceberg[s3fs,pyarrow] \
    kafka-python \
    faker

WORKDIR /opt/dagster/app

# Copy config files
COPY dagster.yaml /opt/dagster/dagster_home/
COPY workspace.yaml /opt/dagster/app/

# Expose webserver port
EXPOSE 3000

ENTRYPOINT ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
