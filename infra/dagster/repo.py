"""KappaLake Dagster assets: Medallion pipeline (bronze -> silver -> gold) on Apache Iceberg (MinIO)."""
import os
import tempfile
import uuid

import airbyte as ab
import pandas as pd
import pyarrow as pa
import s3fs
import trino
from dagster import Definitions, Output, asset
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    DoubleType,
    LongType,
    NestedField,
    StringType,
    TimestampType,
)

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
TRINO_HOST = os.getenv("TRINO_HOST", "trino")
TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))
WAREHOUSE = os.getenv("WAREHOUSE", "s3://warehouse")


# ---------------------------------------------------------------- helpers ---

def _trino_conn():
    return trino.dbapi.connect(
        host=TRINO_HOST,
        port=TRINO_PORT,
        user="admin",
        catalog="iceberg",
        schema="default",
        http_scheme="http",
    )


def _exec(sql: str):
    """Run a Trino statement against the Iceberg catalog; return rows or None."""
    conn = _trino_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall() if cur.description else None
        conn.commit()
        return rows
    finally:
        cur.close()
        conn.close()


def _iceberg_catalog() -> SqlCatalog:
    """Local SqlCatalog that writes Iceberg tables to MinIO (S3FileIO)."""
    db = os.path.join(tempfile.gettempdir(), f"kappalake_iceberg_{uuid.uuid4().hex[:8]}.db")
    props = {
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.access-key-id": MINIO_ACCESS_KEY,
        "s3.secret-access-key": MINIO_SECRET_KEY,
        "s3.path-style-access": "true",
        "s3.region": "us-east-1",
    }
    return SqlCatalog("kappalake", uri=f"sqlite:///{db}", warehouse=WAREHOUSE, **props)


def _iceberg_schema_from_df(df: pd.DataFrame) -> Schema:
    fields = []
    for i, (col, dtype) in enumerate(df.dtypes.items(), start=1):
        col = str(col)
        if pd.api.types.is_integer_dtype(dtype):
            ftype = LongType()
        elif pd.api.types.is_float_dtype(dtype):
            ftype = DoubleType()
        elif pd.api.types.is_datetime64_any_dtype(dtype):
            ftype = TimestampType()
        else:
            ftype = StringType()
        fields.append(NestedField(i, col, ftype, required=False))
    return Schema(*fields)


# ------------------------------------------------------------------- assets ---

@asset
def bronze_users():
    """Ingest faker users into the Iceberg bronze layer on MinIO (PyIceberg)."""
    source = ab.get_source("source-faker", config={"count": 100, "seed": 123}, install_if_missing=True)
    source.select_streams(["users"])
    cache = ab.get_default_cache()
    result = source.read(cache=cache)
    df = result["users"].to_pandas()

    # Purge any previous table files so register_table sees a single latest metadata.
    fs = s3fs.S3FileSystem(
        key=MINIO_ACCESS_KEY,
        secret=MINIO_SECRET_KEY,
        client_kwargs={"endpoint_url": MINIO_ENDPOINT},
    )
    table_loc = f"{WAREHOUSE}/bronze/users"
    if fs.exists(table_loc):
        for f in fs.find(table_loc):
            fs.rm_file(f)

    catalog = _iceberg_catalog()
    catalog.create_namespace_if_not_exists("bronze")
    try:
        catalog.drop_table("bronze.users")
    except Exception:
        pass
    table = catalog.create_table("bronze.users", schema=_iceberg_schema_from_df(df))
    # PyIceberg needs timestamp[us]: normalize pandas datetime64 columns.
    for col in df.select_dtypes(include=["datetime64[ns]"]).columns:
        df[col] = df[col].astype("datetime64[us]")
    table.append(pa.Table.from_pandas(df))

    # Register the freshly written table in Trino's JDBC Iceberg catalog.
    try:
        _exec("CALL iceberg.system.unregister_table(schema_name => 'bronze', table_name => 'users')")
    except Exception:
        pass
    _exec(
        f"CALL iceberg.system.register_table(schema_name => 'bronze', table_name => 'users', "
        f"table_location => '{WAREHOUSE}/bronze/users')"
    )
    rows = _exec("SELECT count(*) FROM iceberg.bronze.users")
    count = rows[0][0] if rows else 0
    return Output(
        value={"num_rows": count, "table": f"{WAREHOUSE}/bronze/users", "columns": list(df.columns)},
        metadata={"num_rows": count, "columns": ", ".join(str(c) for c in df.columns)},
    )


@asset(deps=[bronze_users])
def silver_users():
    """Curate bronze.users into silver.users (typed + cleaned)."""
    _exec("CREATE SCHEMA IF NOT EXISTS iceberg.silver")
    _exec(
        """
        CREATE OR REPLACE TABLE iceberg.silver.users AS
        SELECT
            TRY_CAST("id" AS BIGINT) AS id,
            TRIM("name") AS name,
            LOWER("email") AS email,
            TRY_CAST("age" AS BIGINT) AS age,
            TRIM("gender") AS gender,
            TRIM("nationality") AS nationality,
            TRIM("language") AS language,
            TRIM("occupation") AS occupation,
            TRY_CAST("weight" AS BIGINT) AS weight,
            TRY_CAST("created_at" AS TIMESTAMP) AS created_at,
            TRY_CAST("updated_at" AS TIMESTAMP) AS updated_at
        FROM iceberg.bronze.users
        """
    )
    rows = _exec("SELECT count(*) FROM iceberg.silver.users")
    count = rows[0][0] if rows else 0
    return Output(value={"num_rows": count}, metadata={"num_rows": count})


@asset(deps=[silver_users])
def gold_user_stats():
    """Aggregate silver.users into gold.user_stats (consumption layer)."""
    _exec("CREATE SCHEMA IF NOT EXISTS iceberg.gold")
    _exec(
        """
        CREATE OR REPLACE TABLE iceberg.gold.user_stats AS
        SELECT
            nationality,
            COUNT(*) AS num_users,
            COUNT(DISTINCT language) AS num_languages,
            ROUND(AVG(age), 1) AS avg_age
        FROM iceberg.silver.users
        GROUP BY nationality
        """
    )
    rows = _exec("SELECT count(*) FROM iceberg.gold.user_stats")
    count = rows[0][0] if rows else 0
    return Output(value={"num_rows": count}, metadata={"num_rows": count})


defs = Definitions(assets=[bronze_users, silver_users, gold_user_stats])
