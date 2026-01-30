FROM python:3.10-slim

ENV DAGSTER_HOME=/opt/dagster/dagster_home

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    libpq-dev \
    gcc \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Create directory structure
RUN mkdir -p /opt/dagster/dagster_home /opt/dagster/app

# Install Python dependencies
# dagster-postgres: for storage
# dagster-aws: for S3/MinIO IO managers
# dagster-webserver: for the UI
# dagster-graphql: required by webserver
# airbyte: for ingestion assets
RUN pip install \
    dagster \
    dagster-webserver \
    dagster-postgres \
    dagster-aws \
    dagster-docker \
    psycopg2 \
    airbyte \
    duckdb==0.9.2 \
    duckdb-engine==0.9.2

WORKDIR /opt/dagster/app

# Copy config files
COPY dagster.yaml /opt/dagster/dagster_home/
COPY workspace.yaml /opt/dagster/app/

# Expose webserver port
EXPOSE 3000

ENTRYPOINT ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]

