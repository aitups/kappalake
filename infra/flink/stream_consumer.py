"""KappaLake streaming consumer: Redpanda 'users' -> Iceberg bronze.users_stream (MinIO)."""
import json
import os
import tempfile
import time
import uuid
from datetime import datetime, timezone

import pandas as pd
import pyarrow as pa
import s3fs
import trino
from kafka import KafkaConsumer
from pyiceberg.catalog.sql import SqlCatalog

REDPANDA_BOOTSTRAP = os.getenv("REDPANDA_BOOTSTRAP", "redpanda:29092")
TOPIC = "users"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
TRINO_HOST = os.getenv("TRINO_HOST", "trino")
TRINO_PORT = int(os.getenv("TRINO_PORT", "8080"))
WAREHOUSE = os.getenv("WAREHOUSE", "s3://warehouse")
FLUSH_INTERVAL = float(os.getenv("FLUSH_INTERVAL_SECONDS", "30"))

SCHEMA = [
    ("id", "long"),
    ("name", "string"),
    ("email", "string"),
    ("age", "long"),
    ("gender", "string"),
    ("nationality", "string"),
    ("language", "string"),
    ("occupation", "string"),
    ("created_at", "string"),
]


def _trino_exec(sql: str):
    conn = trino.dbapi.connect(
        host=TRINO_HOST, port=TRINO_PORT, user="admin", catalog="iceberg", schema="default", http_scheme="http"
    )
    cur = conn.cursor()
    try:
        cur.execute(sql)
        rows = cur.fetchall() if cur.description else None
        conn.commit()
        return rows
    finally:
        cur.close()
        conn.close()


def _flush(records):
    if not records:
        return
    df = pd.DataFrame(records)
    db = os.path.join(tempfile.gettempdir(), f"stream_{uuid.uuid4().hex[:8]}.db")
    props = {
        "s3.endpoint": MINIO_ENDPOINT,
        "s3.access-key-id": MINIO_ACCESS_KEY,
        "s3.secret-access-key": MINIO_SECRET_KEY,
        "s3.path-style-access": "true",
        "s3.region": "us-east-1",
    }
    catalog = SqlCatalog("kappalake_stream", uri=f"sqlite:///{db}", warehouse=WAREHOUSE, **props)
    catalog.create_namespace_if_not_exists("bronze")
    table_loc = f"{WAREHOUSE}/bronze/users_stream"
    fs = s3fs.S3FileSystem(key=MINIO_ACCESS_KEY, secret=MINIO_SECRET_KEY, client_kwargs={"endpoint_url": MINIO_ENDPOINT})
    if fs.exists(table_loc):
        for f in fs.find(table_loc):
            fs.rm_file(f)
    try:
        catalog.drop_table("bronze.users_stream")
    except Exception:
        pass
    from pyiceberg.schema import Schema
    from pyiceberg.types import LongType, NestedField, StringType

    schema = Schema(*[NestedField(i, name, LongType() if typ == "long" else StringType(), required=False) for i, (name, typ) in enumerate(SCHEMA, start=1)])
    table = catalog.create_table("bronze.users_stream", schema=schema)
    table.append(pa.Table.from_pandas(df))
    try:
        _trino_exec("CALL iceberg.system.unregister_table(schema_name => 'bronze', table_name => 'users_stream')")
    except Exception:
        pass
    _trino_exec(
        f"CALL iceberg.system.register_table(schema_name => 'bronze', table_name => 'users_stream', "
        f"table_location => '{WAREHOUSE}/bronze/users_stream')"
    )
    print(f"Flushed {len(records)} records to bronze.users_stream")


def main():
    print(f"Consuming '{TOPIC}' from {REDPANDA_BOOTSTRAP}")
    consumer = KafkaConsumer(
        TOPIC,
        bootstrap_servers=REDPANDA_BOOTSTRAP,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        auto_offset_reset="earliest",
        group_id="kappalake-stream",
        consumer_timeout_ms=1000,
    )
    batch = []
    last_flush = time.time()
    while True:
        for msg in consumer:
            batch.append(msg.value)
            if time.time() - last_flush >= FLUSH_INTERVAL or len(batch) >= 100:
                _flush(batch)
                batch = []
                last_flush = time.time()
        # No message within timeout: flush what we have
        if batch and time.time() - last_flush >= FLUSH_INTERVAL:
            _flush(batch)
            batch = []
            last_flush = time.time()
        time.sleep(2)


if __name__ == "__main__":
    main()
