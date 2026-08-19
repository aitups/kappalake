-- Flink SQL: Kafka source ('users' topic) -> Iceberg sink (bronze.users_stream).
CREATE TABLE users_kafka (
  id BIGINT,
  name STRING,
  email STRING,
  age BIGINT,
  gender STRING,
  nationality STRING,
  language STRING,
  occupation STRING,
  created_at STRING,
  ts TIMESTAMP(3) METADATA FROM 'timestamp' VIRTUAL,
  WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'users',
  'properties.bootstrap.servers' = 'redpanda:29092',
  'properties.group.id' = 'flink-stream',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json'
);

CREATE TABLE IF NOT EXISTS iceberg_catalog.bronze.users_stream (
  id BIGINT,
  name STRING,
  email STRING,
  age BIGINT,
  gender STRING,
  nationality STRING,
  language STRING,
  occupation STRING,
  created_at STRING
);

INSERT INTO iceberg_catalog.bronze.users_stream
SELECT id, name, email, age, gender, nationality, language, occupation, created_at
FROM users_kafka;
